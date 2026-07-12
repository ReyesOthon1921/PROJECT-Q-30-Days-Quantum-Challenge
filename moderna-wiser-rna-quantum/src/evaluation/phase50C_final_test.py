"""Phase 50C one-time frozen final-test evaluator.

The evaluator compares the frozen Phase 50A baseline and the locked Phase 50B
objective under exactly the same solver budget on the eight frozen Phase 50
``final_test`` sequences. It has no split-selection or tuning interface.

A registry prevents accidental repeated consumption. A run interrupted after
registry creation may resume only when both the run ID and SHA-256 run signature
match the original attempt. Completed final-test runs cannot be repeated.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.phase50B_equal_budget_audit import (  # noqa: E402
    DELTA_FIELDS,
    SUMMARY_FIELDS,
    _read_csv,
    _resolve,
    _run_variant,
    _safe_id,
    _write_csv,
    _write_json,
    _write_yaml,
    load_strict,
    paired_deltas,
)

DEFAULT_CONFIG: dict[str, Any] = {
    "dataset_path": "data/benchmarks/phase50_solver_diagnostics_sequences.csv",
    "locked_objective_config_path": "configs/phase50B_locked_objective_config.yaml",
    "lock_decision_path": "configs/phase50B_lock_decision.json",
    "output_root": "results/phase50C_final_test",
    "required_lock_tag": "phase50B-objective-locked",
    "required_branch": "phase50C-final-test",
    "expected_final_test_count": 8,
    "expected_locked_variant_id": "short2_penalty_3",
    "exact_max_variables": 20,
    "optimal_structure_capture_limit": 2048,
    "resume": True,
    "budget": {
        "sa_seeds": [3, 7, 11, 19, 23, 29, 31, 37, 41, 43, 47, 53],
        "sa_steps": 6000,
        "sa_initial_temperature": 10.0,
        "sa_final_temperature": 0.01,
        "sa_cooling_rate": 0.995,
        "run_local_refinement": True,
    },
    "baseline_objective": {
        "reward_mode": "sum",
        "short_stem_penalty": 0.0,
        "short_stem_length": 2,
        "min_stem_length": 2,
    },
}

FINAL_SUMMARY_FIELDS = [field for field in SUMMARY_FIELDS if field not in {"rank", "dev_mixed_18_f1"}]
EXPECTED_LOCKED_OBJECTIVE = {
    "reward_mode": "sum",
    "short_stem_penalty": 3.0,
    "short_stem_length": 2,
    "min_stem_length": 2,
}
EVALUATOR_VERSION = "phase50C-final-test-v1"


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


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config["budget"] = dict(DEFAULT_CONFIG["budget"])
    config["baseline_objective"] = dict(DEFAULT_CONFIG["baseline_objective"])
    config_path = _resolve(path or "configs/phase50C_final_test.yaml")
    if config_path.exists():
        loaded = _load_yaml(config_path)
        for key, value in loaded.items():
            if key in {"budget", "baseline_objective"} and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    config["config_path"] = str(config_path)
    return config


def load_final_test_dataset(path: str | Path, expected_count: int) -> list[dict[str, str]]:
    rows = _read_csv(_resolve(path))
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if str(row.get("split", "")).strip().lower() != "final_test":
            continue
        sequence_id = str(row.get("sequence_id", "")).strip()
        sequence = str(row.get("sequence", "")).strip().upper().replace("T", "U")
        if not sequence_id or sequence_id in seen:
            raise ValueError(f"Missing or duplicate final_test sequence_id: {sequence_id}")
        if not sequence:
            raise ValueError(f"Empty final_test sequence: {sequence_id}")
        seen.add(sequence_id)
        result.append({
            "sequence_id": sequence_id,
            "split": "final_test",
            "category": str(row.get("category", "unknown")).strip() or "unknown",
            "source_type": str(row.get("source_type", "synthetic")).strip() or "synthetic",
            "sequence": sequence,
            "notes": str(row.get("notes", "")).strip(),
        })
    if len(result) != int(expected_count):
        raise ValueError(
            f"Expected exactly {expected_count} frozen final_test sequences; found {len(result)}."
        )
    return result


def _git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def verify_lock_state(config: dict[str, Any]) -> dict[str, Any]:
    decision_path = _resolve(config["lock_decision_path"])
    locked_path = _resolve(config["locked_objective_config_path"])
    if not decision_path.exists():
        raise FileNotFoundError(f"Phase 50B lock decision not found: {decision_path}")
    if not locked_path.exists():
        raise FileNotFoundError(f"Phase 50B locked objective config not found: {locked_path}")

    decision = _load_json(decision_path)
    locked = _load_yaml(locked_path)
    expected_variant = str(config["expected_locked_variant_id"])
    if decision.get("lock_recommended") is not True:
        raise RuntimeError("Phase 50B lock decision does not recommend a lock.")
    if decision.get("selected_variant_id") != expected_variant:
        raise RuntimeError(
            f"Lock decision selected {decision.get('selected_variant_id')!r}, expected {expected_variant!r}."
        )
    if decision.get("phase50_final_test_used") is not False:
        raise RuntimeError("Lock decision does not confirm that Phase 50 final_test remained unused.")
    if locked.get("phase50B_objective_variant_id") != expected_variant:
        raise RuntimeError("Locked objective variant ID does not match the Phase 50B decision.")

    objective = locked.get("phase50B_objective")
    if not isinstance(objective, dict):
        raise RuntimeError("Locked objective configuration is missing phase50B_objective.")
    normalized = {
        "reward_mode": str(objective.get("reward_mode")),
        "short_stem_penalty": float(objective.get("short_stem_penalty")),
        "short_stem_length": int(objective.get("short_stem_length")),
        "min_stem_length": int(objective.get("min_stem_length")),
    }
    if normalized != EXPECTED_LOCKED_OBJECTIVE:
        raise RuntimeError(
            f"Locked objective changed after selection: {normalized!r}; expected {EXPECTED_LOCKED_OBJECTIVE!r}."
        )

    required_tag = str(config["required_lock_tag"])
    _git_output("rev-parse", "-q", "--verify", f"refs/tags/{required_tag}")
    required_branch = str(config["required_branch"])
    current_branch = _git_output("branch", "--show-current")
    if current_branch != required_branch:
        raise RuntimeError(
            f"Final-test evaluation must run from branch {required_branch!r}; current branch is {current_branch!r}."
        )
    return {
        "decision_path": str(decision_path),
        "locked_path": str(locked_path),
        "decision": decision,
        "locked": locked,
        "required_tag": required_tag,
        "current_branch": current_branch,
    }


def _canonical_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_run_signature(
    config: dict[str, Any],
    dataset: list[dict[str, str]],
    lock_state: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    payload = {
        "evaluator_version": EVALUATOR_VERSION,
        "dataset": dataset,
        "budget": config["budget"],
        "exact_max_variables": int(config["exact_max_variables"]),
        "optimal_structure_capture_limit": int(config["optimal_structure_capture_limit"]),
        "baseline_objective": config["baseline_objective"],
        "locked_objective": lock_state["locked"].get("phase50B_objective"),
        "locked_variant_id": lock_state["locked"].get("phase50B_objective_variant_id"),
        "lock_decision_sha256": _canonical_hash(lock_state["decision"]),
        "locked_config_sha256": _canonical_hash(lock_state["locked"]),
        "required_tag": lock_state["required_tag"],
    }
    return _canonical_hash(payload), payload


def registry_path(config: dict[str, Any]) -> Path:
    return _resolve(config["output_root"]) / "final_test_registry.json"


def inspect_registry(config: dict[str, Any]) -> dict[str, Any] | None:
    path = registry_path(config)
    return _load_json(path) if path.exists() else None


def begin_or_resume_registry(
    config: dict[str, Any],
    run_id: str,
    signature: str,
    payload: dict[str, Any],
) -> tuple[Path, bool]:
    path = registry_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = inspect_registry(config)
    if existing is None:
        registry = {
            "status": "started",
            "run_id": run_id,
            "run_signature_sha256": signature,
            "signature_payload": payload,
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "completed_at_utc": None,
            "final_test_consumed": True,
        }
        _write_json(path, registry)
        return path, False
    if existing.get("status") == "completed":
        raise RuntimeError(
            "The Phase 50 final_test split has already been consumed and completed. "
            f"See {path}."
        )
    if existing.get("status") != "started":
        raise RuntimeError(f"Unrecognized final-test registry status in {path}.")
    if existing.get("run_id") != run_id or existing.get("run_signature_sha256") != signature:
        raise RuntimeError(
            "An interrupted final-test run exists, but the run ID or signature differs. "
            "Only the exact original run may resume."
        )
    return path, True


def complete_registry(path: Path, run_dir: Path, receipt: dict[str, Any]) -> None:
    registry = _load_json(path)
    registry.update({
        "status": "completed",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(run_dir),
        "final_test_receipt": receipt,
    })
    _write_json(path, registry)


def preflight(config_path: str | Path | None = None) -> dict[str, Any]:
    config = load_config(config_path)
    lock_state = verify_lock_state(config)
    dataset = load_final_test_dataset(config["dataset_path"], int(config["expected_final_test_count"]))
    existing = inspect_registry(config)
    if existing and existing.get("status") == "completed":
        raise RuntimeError("Final-test registry already reports a completed evaluation.")
    result = {
        "ready": True,
        "final_test_sequence_count": len(dataset),
        "selected_variant_id": lock_state["locked"]["phase50B_objective_variant_id"],
        "lock_recommended": lock_state["decision"]["lock_recommended"],
        "phase50_final_test_used_before_preflight": False,
        "registry_status": existing.get("status") if existing else "not_created",
        "branch": lock_state["current_branch"],
        "required_tag": lock_state["required_tag"],
    }
    return result


def _summary_delta(locked: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "mixed_mean_best_known_f1",
        "micro_precision",
        "micro_recall",
        "micro_f1",
        "exact_match_rate",
        "false_positives",
        "false_negatives",
        "mean_best_observed_f1",
        "mean_sa_best_energy_hit_rate",
        "mean_sa_unique_structure_count",
        "exact_strict_failure_rate",
        "mean_qubo_variable_count",
        "mean_quadratic_term_count",
        "mean_runtime_seconds",
    ]
    result: dict[str, Any] = {}
    for key in keys:
        left = locked.get(key)
        right = baseline.get(key)
        result[key] = None if left in (None, "") or right in (None, "") else round(float(left) - float(right), 6)
    return result


def _report(
    run_id: str,
    baseline: dict[str, Any],
    locked: dict[str, Any],
    delta: dict[str, Any],
    receipt: dict[str, Any],
    sequence_count: int,
) -> str:
    lines = [
        "# Phase 50C Frozen Final-Test Report",
        "",
        f"- Run ID: `{run_id}`",
        f"- Final-test sequences: {sequence_count}",
        "- Solver budget equal across variants: True",
        "- Locked variant: `short2_penalty_3`",
        "- Objective selection or retuning performed: False",
        "- Final-test split consumed: True",
        "",
        "## Final-test comparison",
        "",
        "| Variant | Mixed mean F1 | Micro F1 | Precision | Recall | Exact match | FP | FN | SA hit rate | Mean variables |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in [baseline, locked]:
        lines.append(
            f"| `{row['variant_id']}` | {row.get('mixed_mean_best_known_f1')} | "
            f"{row.get('micro_f1')} | {row.get('micro_precision')} | {row.get('micro_recall')} | "
            f"{row.get('exact_match_rate')} | {row.get('false_positives')} | {row.get('false_negatives')} | "
            f"{row.get('mean_sa_best_energy_hit_rate')} | {row.get('mean_qubo_variable_count')} |"
        )
    lines.extend([
        "",
        "## Locked-minus-baseline deltas",
        "",
        f"- Mixed mean F1 delta: {delta.get('mixed_mean_best_known_f1')}",
        f"- Micro F1 delta: {delta.get('micro_f1')}",
        f"- False-positive delta: {delta.get('false_positives')}",
        f"- False-negative delta: {delta.get('false_negatives')}",
        f"- Exact-match-rate delta: {delta.get('exact_match_rate')}",
        f"- SA best-energy-hit-rate delta: {delta.get('mean_sa_best_energy_hit_rate')}",
        "",
        "## Frozen-protocol confirmation",
        "",
        "- Phase 50B lock decision verified before execution.",
        "- Git lock tag verified before execution.",
        "- Only the eight frozen `final_test` rows were loaded.",
        "- Baseline and locked objective used the same 12 seeds and 6,000 SA steps.",
        "- No parameter selection, ranking, or objective changes were performed.",
        f"- Receipt SHA-256: `{receipt['receipt_sha256']}`",
        "",
        "## Interpretation boundary",
        "",
        "This is a small synthetic benchmark against ViennaRNA MFE references. It does not establish biological validation, clinical usefulness, physical equivalence between ViennaRNA energies and QUBO scores, or quantum advantage.",
        "",
        "## Reproducibility files",
        "",
        "- `dataset_snapshot.csv`",
        "- `effective_final_test_config.yaml`",
        "- `effective_locked_objective_config.yaml`",
        "- `lock_decision_snapshot.json`",
        "- `final_test_summary.csv`",
        "- `paired_final_test_deltas.csv`",
        "- `final_test_receipt.json`",
        "- per-variant `sequence_summary.csv`, `sa_runs.csv`, and `run_signature.json`",
        "",
    ])
    return "\n".join(lines)


def run_final_test(
    run_id: str | None = None,
    config_path: str | Path | None = None,
    *,
    consume_final_test: bool = False,
) -> dict[str, Any]:
    if not consume_final_test:
        raise RuntimeError(
            "Refusing to consume the frozen final_test split without --consume-final-test. "
            "Run --preflight first."
        )
    config = load_config(config_path)
    lock_state = verify_lock_state(config)
    dataset = load_final_test_dataset(config["dataset_path"], int(config["expected_final_test_count"]))
    safe_run_id = _safe_id(run_id, "phase50C_final_test")
    signature, signature_payload = build_run_signature(config, dataset, lock_state)
    registry, resumed = begin_or_resume_registry(config, safe_run_id, signature, signature_payload)

    output_dir = _resolve(config["output_root"]) / safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "dataset_snapshot.csv", dataset, [
        "sequence_id", "split", "category", "source_type", "sequence", "notes"
    ])
    _write_yaml(output_dir / "effective_final_test_config.yaml", config)
    _write_yaml(output_dir / "effective_locked_objective_config.yaml", lock_state["locked"])
    _write_json(output_dir / "lock_decision_snapshot.json", lock_state["decision"])

    strict = load_strict(config["locked_objective_config_path"])
    variants = [
        {
            "id": "baseline_sum",
            "description": "Frozen Phase 50A baseline evaluated on the final test.",
            "objective": dict(config["baseline_objective"]),
        },
        {
            "id": str(config["expected_locked_variant_id"]),
            "description": "Locked Phase 50B +3 penalty on two-pair stems.",
            "objective": dict(lock_state["locked"]["phase50B_objective"]),
        },
    ]

    summaries: list[dict[str, Any]] = []
    rows_by_variant: dict[str, list[dict[str, Any]]] = {}
    for index, variant in enumerate(variants, start=1):
        print(f"[FINAL TEST {index}/{len(variants)}] {variant['id']}")
        summary, rows = _run_variant(
            variant,
            dataset,
            strict,
            dict(config["budget"]),
            int(config["exact_max_variables"]),
            int(config["optimal_structure_capture_limit"]),
            output_dir / "variants" / variant["id"],
            bool(config.get("resume", True)),
        )
        summaries.append(summary)
        rows_by_variant[variant["id"]] = rows
        if float(summary.get("success_rate") or 0.0) < 0.999999:
            # Do not cache a partially failed variant as resumable-complete. The
            # final-test registry remains "started", so the exact same signed
            # run may retry after the environmental problem is corrected.
            variant_dir = output_dir / "variants" / variant["id"]
            for stale_name in ("config_summary.json", "run_signature.json"):
                stale_path = variant_dir / stale_name
                if stale_path.exists():
                    stale_path.unlink()
            raise RuntimeError(
                f"Final-test variant {variant['id']} did not complete every sequence successfully. "
                "Correct the failure and rerun the exact same command."
            )

    summary_by_id = {str(row["variant_id"]): row for row in summaries}
    baseline = summary_by_id["baseline_sum"]
    locked = summary_by_id[str(config["expected_locked_variant_id"])]
    for row in summaries:
        row.pop("rank", None)
        row.pop("dev_mixed_18_f1", None)
    _write_csv(output_dir / "final_test_summary.csv", summaries, FINAL_SUMMARY_FIELDS)
    paired = paired_deltas(
        rows_by_variant["baseline_sum"],
        rows_by_variant[str(config["expected_locked_variant_id"])],
        str(config["expected_locked_variant_id"]),
    )
    _write_csv(output_dir / "paired_final_test_deltas.csv", paired, DELTA_FIELDS)

    delta = _summary_delta(locked, baseline)
    receipt_core = {
        "run_id": safe_run_id,
        "evaluator_version": EVALUATOR_VERSION,
        "status": "completed",
        "final_test_consumed": True,
        "resumed_after_interruption": resumed,
        "run_signature_sha256": signature,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "sequence_count": len(dataset),
        "baseline_variant_id": "baseline_sum",
        "locked_variant_id": str(config["expected_locked_variant_id"]),
        "lock_tag": lock_state["required_tag"],
        "branch": lock_state["current_branch"],
        "phase49_validation_used": False,
        "phase50_development_used_for_retuning_after_lock": False,
        "objective_selection_performed": False,
        "summary_delta_locked_minus_baseline": delta,
    }
    receipt = dict(receipt_core)
    receipt["receipt_sha256"] = _canonical_hash(receipt_core)
    _write_json(output_dir / "final_test_receipt.json", receipt)
    (output_dir / "final_test_report.md").write_text(
        _report(safe_run_id, baseline, locked, delta, receipt, len(dataset)), encoding="utf-8"
    )
    complete_registry(registry, output_dir, receipt)

    print(f"[OK] Phase 50C final test saved to: {output_dir}")
    print(f"[OK] Final-test sequences: {len(dataset)}/{len(dataset)}")
    print(f"[OK] Locked objective micro F1: {locked.get('micro_f1')}")
    print(f"[OK] Baseline micro F1: {baseline.get('micro_f1')}")
    print("[OK] Final-test split is now consumed. Further runs are refused.")
    return {
        "output_dir": str(output_dir),
        "baseline_summary": baseline,
        "locked_summary": locked,
        "delta": delta,
        "receipt": receipt,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the one-time Phase 50C frozen final-test evaluation."
    )
    parser.add_argument("--run-id")
    parser.add_argument("--config", default="configs/phase50C_final_test.yaml")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--consume-final-test", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.preflight:
            result = preflight(args.config)
            print(json.dumps(result, indent=2, sort_keys=True))
            print("[OK] Preflight completed without consuming final_test.")
            return 0
        run_final_test(
            run_id=args.run_id,
            config_path=args.config,
            consume_final_test=bool(args.consume_final_test),
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
