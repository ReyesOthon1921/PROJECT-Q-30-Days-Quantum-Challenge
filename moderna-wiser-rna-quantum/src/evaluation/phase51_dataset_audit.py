"""Phase 51A external-dataset declaration and leakage audit.

This module performs no RNA optimization experiments. It validates a newly
assembled external dataset, verifies the frozen Phase 50 objective state, checks
for exact sequence leakage against prior local datasets, and writes a checksum
lock for the later Phase 51 frozen comparison.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.classical.dotbracket_tools import (  # noqa: E402
    dotbracket_to_pairs,
    validate_dotbracket,
)

REQUIRED_COLUMNS = [
    "sequence_id",
    "sequence",
    "reference_structure",
    "category",
    "source_name",
    "source_record_id",
    "source_url",
    "reference_method",
    "split",
    "notes",
]

EXPECTED_LOCKED_OBJECTIVE = {
    "reward_mode": "sum",
    "short_stem_penalty": 3.0,
    "short_stem_length": 2,
    "min_stem_length": 2,
}

DEFAULT_CONFIG: dict[str, Any] = {
    "dataset_path": "data/external/phase51_external_dataset.csv",
    "template_path": "data/external/phase51_external_dataset_template.csv",
    "output_root": "results/phase51_dataset_audit",
    "required_branch": "phase51-external-generalization",
    "required_tags": ["phase50B-objective-locked", "phase50C-complete"],
    "locked_objective_config_path": "configs/phase50B_locked_objective_config.yaml",
    "final_test_registry_snapshot_path": "docs/phase50C_evidence/final_test_registry.json",
    "prior_dataset_paths": [
        "data/benchmarks/phase49_rna_sequences.csv",
        "data/benchmarks/phase50_solver_diagnostics_sequences.csv",
        "data/rna_validation_dataset.csv",
    ],
    "required_split": "external_test",
    "minimum_sequence_count": 12,
    "minimum_category_count": 4,
    "minimum_length": 12,
    "maximum_length": 80,
    "required_length_bins": ["short", "medium", "long"],
    "length_bins": {
        "short": [12, 29],
        "medium": [30, 49],
        "long": [50, 80],
    },
    "allow_wobble": True,
    "require_canonical_or_wobble_pairs": True,
}

AUDITOR_VERSION = "phase51A-dataset-audit-v1"


def _resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml  # type: ignore

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header: {path}")
        return [
            {str(key): "" if value is None else str(value) for key, value in row.items()}
            for row in reader
        ]


def _write_csv(path: Path, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _raw_file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config["required_tags"] = list(DEFAULT_CONFIG["required_tags"])
    config["prior_dataset_paths"] = list(DEFAULT_CONFIG["prior_dataset_paths"])
    config["required_length_bins"] = list(DEFAULT_CONFIG["required_length_bins"])
    config["length_bins"] = {
        key: list(value) for key, value in DEFAULT_CONFIG["length_bins"].items()
    }
    config_path = _resolve(path or "configs/phase51_external_dataset_audit.yaml")
    if config_path.exists():
        loaded = _load_yaml(config_path)
        for key, value in loaded.items():
            if key == "length_bins" and isinstance(value, dict):
                config[key] = {str(k): list(v) for k, v in value.items()}
            else:
                config[key] = value
    config["config_path"] = str(config_path)
    return config


def normalize_sequence(raw: str) -> str:
    sequence = "".join(str(raw).split()).upper()
    if not sequence:
        raise ValueError("sequence is empty")
    invalid = sorted(set(sequence) - set("AUGC"))
    if invalid:
        raise ValueError(
            "sequence contains non-RNA symbols: " + ", ".join(invalid)
        )
    return sequence


def normalize_prior_sequence(raw: str) -> str:
    return "".join(str(raw).split()).upper().replace("T", "U")


def classify_length(length: int, bins: dict[str, list[int]]) -> str:
    matches = [name for name, bounds in bins.items() if int(bounds[0]) <= length <= int(bounds[1])]
    if len(matches) != 1:
        return "out_of_range" if not matches else "ambiguous"
    return matches[0]


def _allowed_pairs(allow_wobble: bool) -> set[str]:
    pairs = {"AU", "UA", "GC", "CG"}
    if allow_wobble:
        pairs.update({"GU", "UG"})
    return pairs


def validate_external_rows(
    rows: list[dict[str, str]],
    config: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str]]:
    normalized_rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: dict[str, int] = {}
    seen_sequences: dict[str, int] = {}
    seen_source_records: dict[tuple[str, str], int] = {}
    required_split = str(config["required_split"]).strip().lower()
    allowed_pairs = _allowed_pairs(bool(config["allow_wobble"]))

    for row_number, row in enumerate(rows, start=2):
        missing_values = [
            field for field in REQUIRED_COLUMNS if field != "notes" and not str(row.get(field, "")).strip()
        ]
        for field in missing_values:
            message = f"row {row_number}: required field {field!r} is empty"
            errors.append(message)
            issues.append({"row_number": row_number, "sequence_id": row.get("sequence_id", ""), "issue_type": "missing_field", "detail": message})

        sequence_id = str(row.get("sequence_id", "")).strip()
        category = str(row.get("category", "")).strip()
        split = str(row.get("split", "")).strip().lower()
        source_name = str(row.get("source_name", "")).strip()
        source_record_id = str(row.get("source_record_id", "")).strip()
        source_url = str(row.get("source_url", "")).strip()
        reference_method = str(row.get("reference_method", "")).strip()
        structure = "".join(str(row.get("reference_structure", "")).split())

        try:
            sequence = normalize_sequence(row.get("sequence", ""))
        except ValueError as exc:
            sequence = normalize_prior_sequence(row.get("sequence", ""))
            message = f"row {row_number} ({sequence_id or 'missing-id'}): {exc}"
            errors.append(message)
            issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "invalid_sequence", "detail": message})

        if sequence_id:
            if sequence_id in seen_ids:
                message = f"duplicate sequence_id {sequence_id!r} at rows {seen_ids[sequence_id]} and {row_number}"
                errors.append(message)
                issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "duplicate_sequence_id", "detail": message})
            else:
                seen_ids[sequence_id] = row_number

        if sequence:
            if sequence in seen_sequences:
                message = f"duplicate sequence at rows {seen_sequences[sequence]} and {row_number}"
                errors.append(message)
                issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "duplicate_sequence", "detail": message})
            else:
                seen_sequences[sequence] = row_number

        source_key = (source_name.lower(), source_record_id.lower())
        if source_name and source_record_id:
            if source_key in seen_source_records:
                message = (
                    f"duplicate source record ({source_name!r}, {source_record_id!r}) "
                    f"at rows {seen_source_records[source_key]} and {row_number}"
                )
                errors.append(message)
                issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "duplicate_source_record", "detail": message})
            else:
                seen_source_records[source_key] = row_number

        if split and split != required_split:
            message = f"row {row_number} ({sequence_id}): split must be {required_split!r}, found {split!r}"
            errors.append(message)
            issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "invalid_split", "detail": message})

        if sequence:
            length = len(sequence)
            if length < int(config["minimum_length"]) or length > int(config["maximum_length"]):
                message = (
                    f"row {row_number} ({sequence_id}): sequence length {length} is outside "
                    f"[{config['minimum_length']}, {config['maximum_length']}]"
                )
                errors.append(message)
                issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "length_out_of_range", "detail": message})
        else:
            length = 0

        valid_structure = bool(structure) and validate_dotbracket(structure)
        if not valid_structure:
            message = f"row {row_number} ({sequence_id}): invalid simple dot-bracket reference"
            errors.append(message)
            issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "invalid_dotbracket", "detail": message})
        elif len(structure) != length:
            message = (
                f"row {row_number} ({sequence_id}): sequence length {length} does not match "
                f"reference length {len(structure)}"
            )
            errors.append(message)
            issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "length_mismatch", "detail": message})
        elif bool(config["require_canonical_or_wobble_pairs"]):
            for left, right in dotbracket_to_pairs(structure):
                pair = sequence[left] + sequence[right]
                if pair not in allowed_pairs:
                    message = (
                        f"row {row_number} ({sequence_id}): reference pair {(left, right)} "
                        f"uses unsupported bases {pair!r}"
                    )
                    errors.append(message)
                    issues.append({"row_number": row_number, "sequence_id": sequence_id, "issue_type": "unsupported_reference_pair", "detail": message})

        length_bin = classify_length(length, config["length_bins"]) if length else "out_of_range"
        normalized_rows.append(
            {
                "sequence_id": sequence_id,
                "sequence": sequence,
                "reference_structure": structure,
                "category": category,
                "source_name": source_name,
                "source_record_id": source_record_id,
                "source_url": source_url,
                "reference_method": reference_method,
                "split": split,
                "notes": str(row.get("notes", "")).strip(),
                "sequence_length": length,
                "length_bin": length_bin,
            }
        )

    if len(rows) < int(config["minimum_sequence_count"]):
        errors.append(
            f"dataset contains {len(rows)} rows; minimum is {config['minimum_sequence_count']}"
        )
    category_count = len({row["category"] for row in normalized_rows if row["category"]})
    if category_count < int(config["minimum_category_count"]):
        errors.append(
            f"dataset contains {category_count} categories; minimum is {config['minimum_category_count']}"
        )
    observed_bins = {row["length_bin"] for row in normalized_rows}
    for required_bin in config["required_length_bins"]:
        if required_bin not in observed_bins:
            errors.append(f"required length bin {required_bin!r} is not represented")

    if any(row["length_bin"] == "ambiguous" for row in normalized_rows):
        warnings.append("one or more configured length bins overlap")

    return normalized_rows, issues, errors, warnings


def build_prior_inventory(config: dict[str, Any]) -> list[dict[str, str]]:
    inventory: list[dict[str, str]] = []
    for raw_path in config["prior_dataset_paths"]:
        path = _resolve(raw_path)
        if not path.exists():
            raise FileNotFoundError(f"prior dataset required for leakage audit is missing: {path}")
        rows = _read_csv(path)
        for row_number, row in enumerate(rows, start=2):
            raw_sequence = row.get("sequence", "")
            sequence = normalize_prior_sequence(raw_sequence)
            if not sequence:
                continue
            inventory.append(
                {
                    "source_path": _display_path(path),
                    "source_row": str(row_number),
                    "sequence_id": str(row.get("sequence_id", "")).strip(),
                    "split": str(row.get("split", row.get("dataset_group", ""))).strip(),
                    "sequence": sequence,
                    "sequence_sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest(),
                }
            )

    registry_path = _resolve(config["final_test_registry_snapshot_path"])
    if registry_path.exists():
        registry = _load_json(registry_path)
        dataset = registry.get("signature_payload", {}).get("dataset", [])
        if isinstance(dataset, list):
            for index, row in enumerate(dataset, start=1):
                if not isinstance(row, dict):
                    continue
                sequence = normalize_prior_sequence(row.get("sequence", ""))
                if not sequence:
                    continue
                inventory.append(
                    {
                        "source_path": _display_path(registry_path),
                        "source_row": str(index),
                        "sequence_id": str(row.get("sequence_id", "")).strip(),
                        "split": str(row.get("split", "final_test")).strip(),
                        "sequence": sequence,
                        "sequence_sha256": hashlib.sha256(sequence.encode("ascii")).hexdigest(),
                    }
                )
    return inventory


def find_leakage(
    external_rows: list[dict[str, Any]],
    prior_inventory: list[dict[str, str]],
) -> list[dict[str, Any]]:
    by_sequence: dict[str, list[dict[str, str]]] = {}
    by_id: dict[str, list[dict[str, str]]] = {}
    for row in prior_inventory:
        by_sequence.setdefault(row["sequence"], []).append(row)
        if row["sequence_id"]:
            by_id.setdefault(row["sequence_id"].lower(), []).append(row)

    leakage: list[dict[str, Any]] = []
    for row in external_rows:
        sequence_id = str(row["sequence_id"])
        for prior in by_sequence.get(str(row["sequence"]), []):
            leakage.append(
                {
                    "external_sequence_id": sequence_id,
                    "leakage_type": "exact_sequence",
                    "prior_sequence_id": prior["sequence_id"],
                    "prior_split": prior["split"],
                    "prior_source_path": prior["source_path"],
                    "prior_source_row": prior["source_row"],
                    "detail": "external sequence exactly matches a previously used sequence",
                }
            )
        for prior in by_id.get(sequence_id.lower(), []):
            leakage.append(
                {
                    "external_sequence_id": sequence_id,
                    "leakage_type": "sequence_id_reuse",
                    "prior_sequence_id": prior["sequence_id"],
                    "prior_split": prior["split"],
                    "prior_source_path": prior["source_path"],
                    "prior_source_row": prior["source_row"],
                    "detail": "external sequence_id reuses a previous local identifier",
                }
            )
    return leakage


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def verify_frozen_state(config: dict[str, Any]) -> dict[str, Any]:
    current_branch = _git_output("branch", "--show-current")
    if current_branch != str(config["required_branch"]):
        raise RuntimeError(
            f"Phase 51 dataset audit must run from branch {config['required_branch']!r}; "
            f"current branch is {current_branch!r}."
        )

    verified_tags: list[str] = []
    for tag in config["required_tags"]:
        _git_output("rev-parse", "-q", "--verify", f"refs/tags/{tag}")
        verified_tags.append(str(tag))

    locked_path = _resolve(config["locked_objective_config_path"])
    if not locked_path.exists():
        raise FileNotFoundError(f"locked objective config not found: {locked_path}")
    locked = _load_yaml(locked_path)
    objective = locked.get("phase50B_objective")
    normalized = {
        "reward_mode": str((objective or {}).get("reward_mode")),
        "short_stem_penalty": float((objective or {}).get("short_stem_penalty")),
        "short_stem_length": int((objective or {}).get("short_stem_length")),
        "min_stem_length": int((objective or {}).get("min_stem_length")),
    }
    if locked.get("phase50B_objective_variant_id") != "short2_penalty_3":
        raise RuntimeError("locked objective variant is not short2_penalty_3")
    if normalized != EXPECTED_LOCKED_OBJECTIVE:
        raise RuntimeError(
            f"locked objective changed: {normalized!r}; expected {EXPECTED_LOCKED_OBJECTIVE!r}"
        )

    registry_path = _resolve(config["final_test_registry_snapshot_path"])
    if not registry_path.exists():
        raise FileNotFoundError(f"tracked Phase 50C registry snapshot not found: {registry_path}")
    registry = _load_json(registry_path)
    if registry.get("status") != "completed" or registry.get("final_test_consumed") is not True:
        raise RuntimeError("Phase 50C registry snapshot is not a completed consumed final test")

    return {
        "branch": current_branch,
        "verified_tags": verified_tags,
        "locked_objective": normalized,
        "locked_objective_sha256": _canonical_hash(locked),
        "phase50C_registry_sha256": _canonical_hash(registry),
        "phase50C_final_test_consumed": True,
    }


def _profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(str(row["category"]) for row in rows)
    length_bin_counts = Counter(str(row["length_bin"]) for row in rows)
    lengths = [int(row["sequence_length"]) for row in rows]
    reference_methods = Counter(str(row["reference_method"]) for row in rows)
    source_names = Counter(str(row["source_name"]) for row in rows)
    return {
        "sequence_count": len(rows),
        "minimum_length": min(lengths) if lengths else None,
        "maximum_length": max(lengths) if lengths else None,
        "mean_length": round(sum(lengths) / len(lengths), 6) if lengths else None,
        "category_counts": dict(sorted(category_counts.items())),
        "length_bin_counts": dict(sorted(length_bin_counts.items())),
        "reference_method_counts": dict(sorted(reference_methods.items())),
        "source_counts": dict(sorted(source_names.items())),
    }


def audit_dataset(
    dataset_path: str | Path,
    config: dict[str, Any],
    run_id: str,
    *,
    verification_only: bool = False,
) -> dict[str, Any]:
    frozen_state = verify_frozen_state(config)
    path = _resolve(dataset_path)
    raw_rows = _read_csv(path)

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
    missing_columns = [field for field in REQUIRED_COLUMNS if field not in header]
    extra_columns = [field for field in header if field not in REQUIRED_COLUMNS]
    if missing_columns:
        raise ValueError(f"dataset is missing required columns: {missing_columns}")

    normalized_rows, row_issues, errors, warnings = validate_external_rows(raw_rows, config)
    if extra_columns:
        warnings.append(f"dataset contains extra columns that will be ignored: {extra_columns}")

    prior_inventory = build_prior_inventory(config)
    leakage = find_leakage(normalized_rows, prior_inventory)
    if leakage:
        errors.append(f"detected {len(leakage)} prior-data leakage match(es)")

    canonical_rows = [
        {field: row.get(field, "") for field in REQUIRED_COLUMNS}
        | {
            "sequence_length": row["sequence_length"],
            "length_bin": row["length_bin"],
        }
        for row in sorted(normalized_rows, key=lambda item: str(item["sequence_id"]))
    ]
    canonical_dataset_sha256 = _canonical_hash(canonical_rows)
    raw_dataset_sha256 = _raw_file_hash(path)
    profile = _profile(normalized_rows)
    audit_passed = len(errors) == 0

    output_dir = _resolve(config["output_root"]) / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_fields = REQUIRED_COLUMNS + ["sequence_length", "length_bin"]
    _write_csv(output_dir / "dataset_snapshot.csv", canonical_rows, snapshot_fields)
    _write_csv(
        output_dir / "prior_sequence_inventory.csv",
        prior_inventory,
        ["source_path", "source_row", "sequence_id", "split", "sequence", "sequence_sha256"],
    )
    _write_csv(
        output_dir / "leakage_report.csv",
        leakage,
        [
            "external_sequence_id",
            "leakage_type",
            "prior_sequence_id",
            "prior_split",
            "prior_source_path",
            "prior_source_row",
            "detail",
        ],
    )
    _write_csv(
        output_dir / "row_issues.csv",
        row_issues,
        ["row_number", "sequence_id", "issue_type", "detail"],
    )
    _write_json(output_dir / "dataset_profile.json", profile)

    decision = {
        "auditor_version": AUDITOR_VERSION,
        "audit_passed": audit_passed,
        "ready_for_phase51_evaluation": audit_passed and not verification_only,
        "verification_only": verification_only,
        "dataset_path": str(path),
        "sequence_count": len(normalized_rows),
        "canonical_dataset_sha256": canonical_dataset_sha256,
        "raw_dataset_sha256": raw_dataset_sha256,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "leakage_match_count": len(leakage),
        "frozen_state": frozen_state,
        "profile": profile,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output_dir / "audit_decision.json", decision)

    dataset_lock = {
        "auditor_version": AUDITOR_VERSION,
        "dataset_locked": audit_passed and not verification_only,
        "verification_only": verification_only,
        "dataset_path": _display_path(path),
        "canonical_dataset_sha256": canonical_dataset_sha256,
        "raw_dataset_sha256": raw_dataset_sha256,
        "sequence_count": len(normalized_rows),
        "locked_objective_variant_id": "short2_penalty_3",
        "locked_objective": EXPECTED_LOCKED_OBJECTIVE,
        "locked_objective_sha256": frozen_state["locked_objective_sha256"],
        "phase50C_registry_sha256": frozen_state["phase50C_registry_sha256"],
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(output_dir / "dataset_lock.json", dataset_lock)

    report_lines = [
        "# Phase 51A External Dataset Audit",
        "",
        f"- Run ID: `{run_id}`",
        f"- Audit passed: {audit_passed}",
        f"- Verification fixture only: {verification_only}",
        f"- Ready for Phase 51 evaluation: {decision['ready_for_phase51_evaluation']}",
        f"- Sequences: {len(normalized_rows)}",
        f"- Leakage matches: {len(leakage)}",
        f"- Canonical dataset SHA-256: `{canonical_dataset_sha256}`",
        f"- Raw file SHA-256: `{raw_dataset_sha256}`",
        "",
        "## Frozen-state verification",
        "",
        f"- Branch: `{frozen_state['branch']}`",
        f"- Tags: {', '.join(frozen_state['verified_tags'])}",
        "- Locked objective: `short2_penalty_3`",
        "- Phase 50C final test consumed: True",
        "",
        "## Dataset profile",
        "",
        f"- Categories: {profile['category_counts']}",
        f"- Length bins: {profile['length_bin_counts']}",
        f"- Length range: {profile['minimum_length']}–{profile['maximum_length']}",
        "",
        "## Errors",
        "",
    ]
    report_lines.extend([f"- {message}" for message in errors] or ["- None"])
    report_lines.extend(["", "## Warnings", ""])
    report_lines.extend([f"- {message}" for message in warnings] or ["- None"])
    report_lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "Passing this audit establishes declared-data integrity and exact-sequence independence from the configured prior local datasets. It does not establish biological representativeness, clinical utility, physical energy equivalence, or quantum advantage.",
            "",
        ]
    )
    (output_dir / "audit_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    return {"decision": decision, "dataset_lock": dataset_lock, "output_dir": output_dir}


def check_template(config: dict[str, Any]) -> dict[str, Any]:
    path = _resolve(config["template_path"])
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        remaining = list(reader)
    missing = [field for field in REQUIRED_COLUMNS if field not in header]
    extra = [field for field in header if field not in REQUIRED_COLUMNS]
    result = {
        "template_path": str(path),
        "header_valid": not missing and not extra,
        "missing_columns": missing,
        "extra_columns": extra,
        "data_row_count": len(remaining),
        "intentionally_empty": len(remaining) == 0,
    }
    if not result["header_valid"]:
        raise RuntimeError(f"Phase 51 template header is invalid: {result}")
    return result


def _make_hairpin(left: str, loop: str) -> tuple[str, str]:
    complement = {"A": "U", "U": "A", "G": "C", "C": "G"}
    right = "".join(complement[base] for base in reversed(left))
    sequence = left + loop + right
    structure = "(" * len(left) + "." * len(loop) + ")" * len(left)
    return sequence, structure


def create_smoke_fixture(path: Path) -> None:
    rows: list[dict[str, str]] = []
    specs = [
        ("verify_short_01", "A" * 13, "." * 13, "unstructured_control"),
        ("verify_short_02", "C" * 15, "." * 15, "unstructured_control"),
        ("verify_short_03", *_make_hairpin("GCGC", "AAAAA"), "designed_hairpin"),
        ("verify_short_04", *_make_hairpin("AUAUA", "GGGG"), "au_rich"),
        ("verify_medium_01", "ACGU" * 8, "." * 32, "mixed_composition"),
        ("verify_medium_02", "GCAU" * 9, "." * 36, "gc_rich"),
        ("verify_medium_03", "UGCA" * 10, "." * 40, "wobble_enriched"),
        ("verify_medium_04", "AUGC" * 12, "." * 48, "mixed_composition"),
        ("verify_long_01", "AGCU" * 13, "." * 52, "mixed_composition"),
        ("verify_long_02", "CUAG" * 14, "." * 56, "gc_rich"),
        ("verify_long_03", "GUAC" * 15, "." * 60, "wobble_enriched"),
        ("verify_long_04", "UCGA" * 17, "." * 68, "mixed_composition"),
    ]
    for sequence_id, sequence, structure, category in specs:
        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence": sequence,
                "reference_structure": structure,
                "category": category,
                "source_name": "phase51_verification_fixture",
                "source_record_id": sequence_id,
                "source_url": f"local://{sequence_id}",
                "reference_method": "verification_fixture",
                "split": "external_test",
                "notes": "Generated only to verify the Phase 51A audit code; not research data.",
            }
        )
    _write_csv(path, rows, REQUIRED_COLUMNS)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/phase51_external_dataset_audit.yaml")
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--run-id", default="phase51A_dataset_audit_001")
    parser.add_argument("--template-check", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    if args.template_check:
        result = check_template(config)
        print(json.dumps(result, indent=2, sort_keys=True))
        print("[OK] Phase 51 external dataset template is ready for population.")
        return 0

    verification_only = bool(args.smoke)
    if args.smoke:
        fixture_path = _resolve(config["output_root"]) / args.run_id / "verification_fixture.csv"
        fixture_path.parent.mkdir(parents=True, exist_ok=True)
        create_smoke_fixture(fixture_path)
        dataset_path: str | Path = fixture_path
    else:
        dataset_path = args.dataset or config["dataset_path"]

    result = audit_dataset(dataset_path, config, args.run_id, verification_only=verification_only)
    decision = result["decision"]
    print(f"[OK] Phase 51A audit saved to: {result['output_dir']}")
    print(f"[OK] Audit passed: {decision['audit_passed']}")
    print(f"[OK] Verification only: {decision['verification_only']}")
    print(f"[OK] Prior-data leakage matches: {decision['leakage_match_count']}")
    if not decision["audit_passed"]:
        for message in decision["errors"]:
            print(f"[ERROR] {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
