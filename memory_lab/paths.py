"""统一结果文件位置；兼容早期的平铺日志，避免重复读取两份证据。"""

from pathlib import Path

ARTIFACT_GROUPS = {
    "manifest.json": "",
    "api.jsonl": "raw",
    "events.jsonl": "raw",
    "trials.jsonl": "raw",
    "memories.json": "inputs",
    "ground_truth.json": "inputs",
    "schedule.json": "inputs",
    "summary.json": "analysis",
    "summary.csv": "analysis",
    "trials.csv": "analysis",
    "security.png": "analysis",
    "utility.png": "analysis",
    "latency.png": "analysis",
    "validation.json": "analysis",
}


def artifact_path(run_dir: Path, name: str) -> Path:
    group = ARTIFACT_GROUPS[name]
    target = run_dir / group / name if group else run_dir / name
    legacy = run_dir / name
    if target != legacy and target.exists() and legacy.exists():
        raise ValueError(f"Duplicate flat/grouped artifact: {name}")
    return legacy if legacy.exists() else target
