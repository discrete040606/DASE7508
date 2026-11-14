import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .paths import artifact_path
from .models import read_jsonl, write_json
from .runner import latest_trials


def analyze(run_dir: Path):
    manifest = json.loads(artifact_path(run_dir, "manifest.json").read_text())
    schedule = json.loads(artifact_path(run_dir, "schedule.json").read_text())
    trials = latest_trials(run_dir)
    requests = {}
    api_path = artifact_path(run_dir, "api.jsonl")
    for event in read_jsonl(api_path):
        if event.get("event") == "request":
            requests[event["request_id"]] = {"trial_id": event.get("trial_id"), "cost": event["reserved_usd"]}
        elif event.get("event") in ("response", "request_error") and event["request_id"] in requests:
            requests[event["request_id"]]["cost"] = event["cost_upper_usd"]
    # Keep failed attempts in the cost total, even when a later attempt completes.
    all_attempts = list(read_jsonl(artifact_path(run_dir, "trials.jsonl")))
    rows = []
    for slot in schedule:
        trial = trials.get(slot["trial_id"], {})
        rows.append({**slot, "status": trial.get("status", "not_started"),
                     "simulated": manifest["simulated"], "latency_ms": trial.get("latency_ms"),
                     "cost_upper_usd": trial.get("cost_upper_usd", 0), **trial.get("metrics", {})})
    frame = pd.DataFrame(rows)
    artifact_path(run_dir, "summary.csv").parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(artifact_path(run_dir, "trials.csv"), index=False)
    summaries = []
    for condition, group in frame.groupby("condition"):
        summary = {"condition": condition, "planned": len(group),
                   "attempted": int((group.status != "not_started").sum()),
                   "complete": int((group.status == "complete").sum()),
                   "errors": int(group.status.isin(["error", "stopped"]).sum()),
                   "simulated": manifest["simulated"]}
        for verdict, rate in [("l1", "CURR"), ("l2", "CUDR")]:
            vals = group.get(verdict, pd.Series(index=group.index, dtype=float))
            known = vals.dropna()
            positives = int((known == True).sum())
            unknown = len(group) - len(known)
            summary.update({rate: positives / len(known) if len(known) else None,
                            f"{rate}_n": len(known), f"{rate}_positive": positives,
                            f"{rate}_unknown": unknown, f"{rate}_lower": positives / len(group),
                            f"{rate}_upper": (positives + unknown) / len(group)})
        for metric in ["lrsr", "fbr", "precision_at_k", "recall_at_k", "mrr"]:
            vals = group.get(metric, pd.Series(dtype=float)).dropna()
            summary[metric] = float(vals.mean()) if len(vals) else None
            summary[f"{metric}_n"] = len(vals)
        for metric in ["latency_ms", "filter_ms", "retrieval_ms"]:
            vals = group.get(metric, pd.Series(dtype=float)).dropna()
            summary[metric + "_median"] = float(vals.median()) if len(vals) else None
            summary[metric + "_iqr"] = float(vals.quantile(.75) - vals.quantile(.25)) if len(vals) else None
        summary["cost_upper_usd"] = sum(t.get("cost_upper_usd", 0) for t in all_attempts if t["condition"] == condition)
        if requests:
            slot_ids = set(group.trial_id)
            summary["cost_upper_usd"] = sum(r["cost"] for r in requests.values() if r["trial_id"] in slot_ids)
        summaries.append(summary)
    result = pd.DataFrame(summaries)
    result.to_csv(artifact_path(run_dir, "summary.csv"), index=False)
    write_json(artifact_path(run_dir, "summary.json"), summaries)
    prefix = "OFFLINE FIXTURE - NOT RESEARCH RESULTS" if manifest["simulated"] else "LIVE API EXPERIMENT"
    for columns, name, title in [(["CURR", "CUDR"], "security", "Cross-user retrieval and disclosure"),
                                 (["lrsr", "precision_at_k", "recall_at_k", "mrr"], "utility", "Legitimate retrieval quality"),
                                 (["latency_ms_median", "retrieval_ms_median"], "latency", "Median latency (ms)")]:
        plot = result.set_index("condition")[columns].apply(pd.to_numeric, errors="coerce")
        fig, ax = plt.subplots(figsize=(8, 4.5))
        if plot.notna().any().any():
            plot.plot.bar(ax=ax)
        else:
            ax.text(.5, .5, "No evaluable observations", ha="center", transform=ax.transAxes)
        ax.set_title(prefix + "\n" + title)
        ax.set_xlabel("Condition")
        if name != "latency":
            ax.set_ylim(0, 1.05)
        fig.tight_layout()
        fig.savefig(artifact_path(run_dir, f"{name}.png"), dpi=160)
        plt.close(fig)
    return result
