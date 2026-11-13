from __future__ import annotations

import importlib.metadata
import json
import platform
import random
import subprocess
import sys
from pathlib import Path

from .agent import Agent
from .data import load
from .evaluation import evaluate
from .models import Config, SYSTEM_PROMPT, TOOLS, append_jsonl, digest, write_json
from .provider import DeepSeek, MockProvider, exclusive
from .retrieval import Retrieval, Sessions, Store


def slots(cases, config, pilot=False):
    if pilot:
        legal = [c for c in cases if c.kind == "legitimate"][:4]
        attacks = [next(c for c in cases if c.family == f"M{i}") for i in range(1, 9)]
        cases = legal + attacks
    rows = []
    for case in cases:
        for condition in ("A", "C") if case.kind == "legitimate" else ("B", "D"):
            for repetition in range(1 if pilot else config.repetitions):
                rows.append({"trial_id": f"{condition}-{case.case_id}-r{repetition + 1}",
                             "case_id": case.case_id, "condition": condition, "repetition": repetition + 1})
    random.Random(config.seed).shuffle(rows)
    return rows


def manifest(root, config, memories, cases, truth, simulated, pilot):
    packages = {n: importlib.metadata.version(n) for n in
                ["chromadb", "openai", "pydantic", "PyYAML", "pandas", "matplotlib", "streamlit"]}
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except subprocess.CalledProcessError:
        commit = "uncommitted"
    code_files = [root / "pyproject.toml", *sorted((root / "src").rglob("*.py")), *sorted((root / "app").rglob("*.py"))]
    code = {str(p.relative_to(root)): digest(p.read_text()) for p in code_files}
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--untracked-files=normal", "--",
                                "pyproject.toml", "requirements.lock.txt", "src", "app", "configs", "data"], cwd=root,
                                capture_output=True, text=True).stdout.strip())
    lock = root / "requirements.lock.txt"
    model_cache = root / ".model-cache"
    embedding_files = {str(p.relative_to(model_cache)): __import__("hashlib").sha256(p.read_bytes()).hexdigest()
                       for p in sorted(model_cache.rglob('*')) if p.is_file()}
    return {"schema_version": 1, "simulated": simulated, "pilot": pilot, "config": config.model_dump(),
            "memories_sha256": digest(memories), "cases_sha256": digest([c.model_dump() for c in cases]),
            "ground_truth_sha256": digest(truth), "code": code, "commit": commit, "working_tree_dirty": dirty,
            "lock_sha256": digest(lock.read_text()) if lock.exists() else None,
            "python": sys.version, "platform": platform.platform(), "packages": packages,
            "embedding_files": embedding_files, "prompt": SYSTEM_PROMPT, "tools": TOOLS}


def latest_trials(run_dir):
    rows = {}
    schedule_path = run_dir / "schedule.json"
    schedule = {s["trial_id"]: s for s in json.loads(schedule_path.read_text())} if schedule_path.exists() else {}
    truth_path = run_dir / "ground_truth.json"
    truth = json.loads(truth_path.read_text()) if truth_path.exists() else None
    # Replay checkpoints first, then final records. Highest attempt wins; observed
    # positives survive a retry so an interrupted leak cannot become a safe slot.
    for filename in ("events.jsonl", "trials.jsonl"):
        path = run_dir / filename
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            record = json.loads(line)
            row = record.get("trial", record)
            if "trial_id" not in row:
                continue
            row.update(schedule.get(row["trial_id"], {}))
            if truth:
                row["metrics"] = evaluate(row, truth)
            old = rows.get(row["trial_id"])
            chosen = row if old is None or row.get("attempt", 1) >= old.get("attempt", 1) else old
            if old:
                for key in ("l1", "l2"):
                    if old.get("metrics", {}).get(key) is True or row.get("metrics", {}).get(key) is True:
                        chosen["metrics"][key] = True
            rows[row["trial_id"]] = chosen
    return rows


def run(root: Path, config: Config, run_dir: Path, simulated=False, pilot=False, limit=None):
    if simulated and "offline" not in run_dir.parts:
        raise ValueError("Offline fixture output must be under results/offline/")
    if not simulated and "offline" in run_dir.parts:
        raise ValueError("Live evidence must not share an offline output directory")
    if not simulated and not pilot and config.repetitions != 5:
        raise ValueError("Formal experiment requires five repetitions (300 slots)")
    memories, cases, truth = load(root)
    schedule = slots(cases, config, pilot)
    with exclusive(root / ".runtime" / "active.lock"):
        store = Store(root / "chroma_db", memories)
        frozen = manifest(root, config, memories, cases, truth, simulated, pilot)
        if not simulated and not pilot and frozen["working_tree_dirty"]:
            raise ValueError("Commit the experiment code/configuration/data before starting a formal run")
        run_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = run_dir / "manifest.json"
        if manifest_path.exists() and json.loads(manifest_path.read_text()) != frozen:
            raise ValueError("Frozen configuration/data/code/environment changed; create a new run directory")
        write_json(manifest_path, frozen)
        write_json(run_dir / "schedule.json", schedule)
        write_json(run_dir / "ground_truth.json", truth)
        write_json(run_dir / "memories.json", memories)
        existing = latest_trials(run_dir)
        provider = MockProvider() if simulated else DeepSeek(root, config, run_dir / "api.jsonl")
        previous_models = {r["response_model"] for r in existing.values() if r.get("response_model")}
        if len(previous_models) > 1:
            raise ValueError("Mixed response models in evidence")
        provider.response_model = next(iter(previous_models), provider.response_model)
        sessions = Sessions()
        agent = Agent(Retrieval(store, sessions, config.top_k), provider, run_dir / "events.jsonl")
        by_id = {c.case_id: c for c in cases}
        attempted = 0
        for slot in schedule:
            old = existing.get(slot["trial_id"])
            if old and old["status"] == "complete":
                continue
            if limit is not None and attempted >= limit:
                break
            case = by_id[slot["case_id"]]
            trial, _ = agent.run_case(case, sessions.create(case.attacker_user_id), config,
                                      slot["condition"] in ("C", "D"), slot["trial_id"],
                                      attempt=1 + (old or {}).get("attempt", 0))
            trial.update(slot, attempt=1 + (old or {}).get("attempt", 0))
            trial["metrics"] = evaluate(trial, truth)
            append_jsonl(run_dir / "trials.jsonl", trial)
            print(f"{slot['trial_id']}: {trial['status']} L1={trial['metrics']['l1']} L2={trial['metrics']['l2']}", flush=True)
            attempted += 1
            if trial["status"] == "stopped":
                break
        return latest_trials(run_dir)
