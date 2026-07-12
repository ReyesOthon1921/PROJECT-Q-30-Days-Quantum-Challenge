from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

from src.evaluation import phase50C_final_test as final_test


def _write_dataset(path: Path, count: int = 8) -> None:
    rows = [
        {
            "sequence_id": f"test_{index}",
            "split": "final_test",
            "category": "mixed_composition",
            "source_type": "synthetic",
            "sequence": "GCGAAACGC",
            "notes": "frozen",
        }
        for index in range(count)
    ]
    rows.append({
        "sequence_id": "dev_ignore",
        "split": "development",
        "category": "mixed_composition",
        "source_type": "synthetic",
        "sequence": "AAAAAAAAA",
        "notes": "ignored",
    })
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def _lock_files(tmp_path: Path, penalty: float = 3.0) -> tuple[Path, Path]:
    decision = tmp_path / "decision.json"
    locked = tmp_path / "locked.yaml"
    decision.write_text(json.dumps({
        "lock_recommended": True,
        "selected_variant_id": "short2_penalty_3",
        "phase50_final_test_used": False,
    }), encoding="utf-8")
    locked.write_text(yaml.safe_dump({
        "min_loop_length": 3,
        "allow_wobble": True,
        "phase50B_objective_variant_id": "short2_penalty_3",
        "phase50B_objective": {
            "reward_mode": "sum",
            "short_stem_penalty": penalty,
            "short_stem_length": 2,
            "min_stem_length": 2,
        },
    }, sort_keys=False), encoding="utf-8")
    return decision, locked


def _config(tmp_path: Path, dataset: Path, decision: Path, locked: Path) -> dict:
    return {
        **final_test.DEFAULT_CONFIG,
        "dataset_path": str(dataset),
        "lock_decision_path": str(decision),
        "locked_objective_config_path": str(locked),
        "output_root": str(tmp_path / "results"),
        "required_lock_tag": "phase50B-objective-locked",
        "required_branch": "phase50C-final-test",
        "expected_final_test_count": 8,
        "expected_locked_variant_id": "short2_penalty_3",
    }


def test_load_final_test_dataset_reads_only_frozen_rows(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.csv"
    _write_dataset(dataset)
    rows = final_test.load_final_test_dataset(dataset, 8)
    assert len(rows) == 8
    assert {row["split"] for row in rows} == {"final_test"}
    assert all(row["sequence_id"].startswith("test_") for row in rows)


def test_load_final_test_dataset_requires_exact_count(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.csv"
    _write_dataset(dataset, count=7)
    with pytest.raises(ValueError, match="Expected exactly 8"):
        final_test.load_final_test_dataset(dataset, 8)


def test_verify_lock_state_accepts_exact_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = tmp_path / "dataset.csv"
    _write_dataset(dataset)
    decision, locked = _lock_files(tmp_path)
    config = _config(tmp_path, dataset, decision, locked)

    def fake_git(*args: str) -> str:
        return "phase50C-final-test" if args[:2] == ("branch", "--show-current") else "deadbeef"

    monkeypatch.setattr(final_test, "_git_output", fake_git)
    state = final_test.verify_lock_state(config)
    assert state["locked"]["phase50B_objective"]["short_stem_penalty"] == 3.0


def test_verify_lock_state_rejects_changed_objective(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = tmp_path / "dataset.csv"
    _write_dataset(dataset)
    decision, locked = _lock_files(tmp_path, penalty=2.0)
    config = _config(tmp_path, dataset, decision, locked)
    monkeypatch.setattr(final_test, "_git_output", lambda *args: "phase50C-final-test")
    with pytest.raises(RuntimeError, match="Locked objective changed"):
        final_test.verify_lock_state(config)


def test_registry_allows_only_matching_interrupted_resume(tmp_path: Path) -> None:
    config = {**final_test.DEFAULT_CONFIG, "output_root": str(tmp_path / "results")}
    path, resumed = final_test.begin_or_resume_registry(config, "run_1", "abc", {"x": 1})
    assert resumed is False
    assert path.exists()
    _, resumed = final_test.begin_or_resume_registry(config, "run_1", "abc", {"x": 1})
    assert resumed is True
    with pytest.raises(RuntimeError, match="Only the exact original run"):
        final_test.begin_or_resume_registry(config, "run_2", "def", {"x": 2})


def test_completed_registry_refuses_repeat(tmp_path: Path) -> None:
    config = {**final_test.DEFAULT_CONFIG, "output_root": str(tmp_path / "results")}
    path, _ = final_test.begin_or_resume_registry(config, "run_1", "abc", {"x": 1})
    final_test.complete_registry(path, tmp_path / "run", {"receipt_sha256": "hash"})
    with pytest.raises(RuntimeError, match="already been consumed"):
        final_test.begin_or_resume_registry(config, "run_1", "abc", {"x": 1})


def test_run_requires_explicit_consume_flag() -> None:
    with pytest.raises(RuntimeError, match="--consume-final-test"):
        final_test.run_final_test(run_id="phase50C_test", consume_final_test=False)


def test_cli_has_no_split_or_budget_override() -> None:
    parser = final_test.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--split", "final_test"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--steps", "10"])
