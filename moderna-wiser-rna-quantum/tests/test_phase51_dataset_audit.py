from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
import yaml

from src.evaluation import phase51_dataset_audit as audit


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str] | None = None) -> None:
    fields = fields or audit.REQUIRED_COLUMNS
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _base_row(sequence_id: str, sequence: str, structure: str, category: str = "mixed") -> dict[str, str]:
    return {
        "sequence_id": sequence_id,
        "sequence": sequence,
        "reference_structure": structure,
        "category": category,
        "source_name": "fixture_source",
        "source_record_id": sequence_id,
        "source_url": f"https://example.invalid/{sequence_id}",
        "reference_method": "curated_reference",
        "split": "external_test",
        "notes": "test fixture",
    }


def _config(tmp_path: Path) -> dict:
    locked = tmp_path / "locked.yaml"
    locked.write_text(
        yaml.safe_dump(
            {
                "phase50B_objective_variant_id": "short2_penalty_3",
                "phase50B_objective": audit.EXPECTED_LOCKED_OBJECTIVE,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps({"status": "completed", "final_test_consumed": True, "signature_payload": {"dataset": []}}),
        encoding="utf-8",
    )
    prior = tmp_path / "prior.csv"
    _write_csv(
        prior,
        [{"sequence_id": "old", "sequence": "GGGGAAAACCCC"}],
        ["sequence_id", "sequence"],
    )
    return {
        **audit.DEFAULT_CONFIG,
        "locked_objective_config_path": str(locked),
        "final_test_registry_snapshot_path": str(registry),
        "prior_dataset_paths": [str(prior)],
        "output_root": str(tmp_path / "out"),
        "minimum_sequence_count": 3,
        "minimum_category_count": 2,
        "minimum_length": 4,
        "maximum_length": 80,
        "required_length_bins": ["short", "medium", "long"],
        "length_bins": {"short": [4, 19], "medium": [20, 39], "long": [40, 80]},
    }


def _valid_rows() -> list[dict[str, str]]:
    return [
        _base_row("new_short", "AAAAA", ".....", "control"),
        _base_row("new_medium", "ACGU" * 5, "." * 20, "mixed"),
        _base_row("new_long", "AGCU" * 10, "." * 40, "mixed"),
    ]


def test_normalize_sequence_accepts_rna_and_rejects_t() -> None:
    assert audit.normalize_sequence(" a u g c ") == "AUGC"
    with pytest.raises(ValueError, match="non-RNA"):
        audit.normalize_sequence("ATGC")


def test_length_bin_classification() -> None:
    bins = {"short": [4, 19], "medium": [20, 39], "long": [40, 80]}
    assert audit.classify_length(4, bins) == "short"
    assert audit.classify_length(20, bins) == "medium"
    assert audit.classify_length(80, bins) == "long"
    assert audit.classify_length(81, bins) == "out_of_range"


def test_validate_rows_accepts_canonical_hairpin() -> None:
    config = {**audit.DEFAULT_CONFIG, "minimum_sequence_count": 1, "minimum_category_count": 1, "minimum_length": 4, "required_length_bins": [], "length_bins": {"short": [4, 80]}}
    rows = [_base_row("hairpin", "GCGAAAACGC", "(((....)))", "hairpin")]
    normalized, issues, errors, warnings = audit.validate_external_rows(rows, config)
    assert normalized[0]["sequence_length"] == 10
    assert issues == []
    assert errors == []
    assert warnings == []


def test_validate_rows_rejects_noncanonical_pair() -> None:
    config = {**audit.DEFAULT_CONFIG, "minimum_sequence_count": 1, "minimum_category_count": 1, "minimum_length": 4, "required_length_bins": [], "length_bins": {"short": [4, 80]}}
    rows = [_base_row("bad_pair", "AAAA", "(..)", "hairpin")]
    _, _, errors, _ = audit.validate_external_rows(rows, config)
    assert any("unsupported bases" in message for message in errors)


def test_validate_rows_detects_duplicate_sequence_and_id() -> None:
    config = {**audit.DEFAULT_CONFIG, "minimum_sequence_count": 2, "minimum_category_count": 1, "minimum_length": 4, "required_length_bins": [], "length_bins": {"short": [4, 80]}}
    rows = [_base_row("dup", "AAAA", "...."), _base_row("dup", "AAAA", "....")]
    _, _, errors, _ = audit.validate_external_rows(rows, config)
    assert any("duplicate sequence_id" in message for message in errors)
    assert any("duplicate sequence at" in message for message in errors)


def test_find_leakage_detects_exact_sequence_and_id_reuse() -> None:
    external = [{"sequence_id": "old_id", "sequence": "AUGC"}]
    prior = [{"sequence_id": "old_id", "sequence": "AUGC", "split": "development", "source_path": "prior.csv", "source_row": "2"}]
    found = audit.find_leakage(external, prior)
    assert {row["leakage_type"] for row in found} == {"exact_sequence", "sequence_id_reuse"}


def test_canonical_hash_is_order_stable_for_dict_keys() -> None:
    assert audit._canonical_hash({"b": 2, "a": 1}) == audit._canonical_hash({"a": 1, "b": 2})


def test_check_template_accepts_header_only(tmp_path: Path) -> None:
    template = tmp_path / "template.csv"
    _write_csv(template, [])
    result = audit.check_template({**audit.DEFAULT_CONFIG, "template_path": str(template)})
    assert result["header_valid"] is True
    assert result["intentionally_empty"] is True


def test_verify_frozen_state_rejects_changed_objective(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(tmp_path)
    locked_path = Path(config["locked_objective_config_path"])
    locked_path.write_text(
        yaml.safe_dump(
            {
                "phase50B_objective_variant_id": "short2_penalty_3",
                "phase50B_objective": {**audit.EXPECTED_LOCKED_OBJECTIVE, "short_stem_penalty": 2.0},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(audit, "_git_output", lambda *args: "phase51-external-generalization" if args[:2] == ("branch", "--show-current") else "ok")
    with pytest.raises(RuntimeError, match="locked objective changed"):
        audit.verify_frozen_state(config)


def test_full_audit_passes_and_writes_dataset_lock(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(tmp_path)
    dataset = tmp_path / "external.csv"
    _write_csv(dataset, _valid_rows())
    monkeypatch.setattr(audit, "_git_output", lambda *args: "phase51-external-generalization" if args[:2] == ("branch", "--show-current") else "ok")
    result = audit.audit_dataset(dataset, config, "audit_ok")
    assert result["decision"]["audit_passed"] is True
    assert result["decision"]["ready_for_phase51_evaluation"] is True
    lock = json.loads((result["output_dir"] / "dataset_lock.json").read_text(encoding="utf-8"))
    assert lock["dataset_locked"] is True
    assert lock["locked_objective_variant_id"] == "short2_penalty_3"


def test_full_audit_fails_on_prior_sequence_leakage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _config(tmp_path)
    dataset = tmp_path / "external.csv"
    rows = _valid_rows()
    rows[0]["sequence"] = "GGGGAAAACCCC"
    rows[0]["reference_structure"] = "." * 12
    _write_csv(dataset, rows)
    monkeypatch.setattr(audit, "_git_output", lambda *args: "phase51-external-generalization" if args[:2] == ("branch", "--show-current") else "ok")
    result = audit.audit_dataset(dataset, config, "audit_leak")
    assert result["decision"]["audit_passed"] is False
    assert result["decision"]["leakage_match_count"] >= 1
    assert result["dataset_lock"]["dataset_locked"] is False
