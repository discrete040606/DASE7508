import json

import pytest

from memory_lab.models import Config
from memory_lab.paths import artifact_path
from memory_lab.provider import Budget


def test_grouped_layout_and_legacy_compatibility(tmp_path):
    assert artifact_path(tmp_path, "api.jsonl") == tmp_path / "raw/api.jsonl"
    assert artifact_path(tmp_path, "schedule.json") == tmp_path / "inputs/schedule.json"
    assert artifact_path(tmp_path, "summary.csv") == tmp_path / "analysis/summary.csv"
    assert artifact_path(tmp_path, "manifest.json") == tmp_path / "manifest.json"
    old = tmp_path / "trials.jsonl"
    old.write_text("legacy evidence\n")
    assert artifact_path(tmp_path, "trials.jsonl") == old
    (tmp_path / "raw").mkdir()
    (tmp_path / "raw/trials.jsonl").write_text("another copy\n")
    with pytest.raises(ValueError, match="Duplicate"):
        artifact_path(tmp_path, "trials.jsonl")


def test_existing_cost_ledger_is_used_in_local_runtime(tmp_path):
    path = tmp_path / ".local/runtime/budget.json"
    path.parent.mkdir(parents=True)
    state = {
        "spent_upper_usd": 0.2017431,
        "measured_peak_estimate_usd": 0.2017431,
        "reservations": {},
    }
    path.write_text(json.dumps(state))
    budget = Budget(tmp_path, Config())
    assert budget.path == path
    assert budget.read() == state
