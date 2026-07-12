"""Phase 50B.1 equal-budget objective-selection audit.

This module compares the frozen baseline, the +3 two-pair-stem penalty, and
minimum stem length 3 under exactly the same solver budget. It uses only the
Phase 50 development split and has no final-test execution path.

The audit also adds two reproducibility protections missing from the initial
screen/confirmation runner:

1. exact-solver degeneracy is recorded instead of silently treating the first
   minimum-energy assignment as the only optimum;
2. resume is guarded by a run signature so stale results cannot be reused after
   a configuration, dataset, or solver-budget change.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.classical.vienna_rnafold import run_rnafold
from src.evaluation.phase50_solver_diagnostics import run_fast_sa
from src.evaluation.structural_comparison import compare_structures
from src.qubo.objective_variants import (
    build_variant_qubo,
    solve_variant_qubo_exact,
    solve_variant_qubo_greedy,
)
from src.solvers.simulated_annealing import decode_solution_to_structure

DEFAULT_CONFIG: dict[str, Any] = {
    "dataset_path": "data/benchmarks/phase50_solver_diagnostics_sequences.csv",
    "strict_config_path": "configs/phase50_locked_phase49_config.yaml",
    "output_root": "results/phase50B_equal_budget_audit",
    "resume": True,
    "exact_max_variables": 20,
    "optimal_structure_capture_limit": 2048,
    "budget": {
        "sa_seeds": [3, 7, 11, 19, 23, 29, 31, 37, 41, 43, 47, 53],
        "sa_steps": 6000,
        "sa_initial_temperature": 10.0,
        "sa_final_temperature": 0.01,
        "sa_cooling_rate": 0.995,
        "run_local_refinement": True,
    },
    "selection": {
        "baseline_variant_id": "baseline_sum",
        "micro_f1_noninferiority_margin": 0.03,
        "exact_failure_rate_noninferiority_margin": 0.0,
    },
    "variants": [],
}

SEQUENCE_FIELDS = [
    "variant_id", "sequence_id", "category", "sequence_length", "status", "error",
    "reference_structure", "reference_energy", "qubo_variable_count",
    "quadratic_term_count", "exact_status", "exact_energy", "exact_f1",
    "exact_optimal_assignment_count", "exact_captured_optimal_structure_count",
    "exact_optimal_structures_truncated", "exact_optimal_min_f1",
    "exact_optimal_mean_f1", "exact_optimal_max_f1", "exact_optimum_classification",
    "greedy_energy", "greedy_f1", "sa_best_energy", "sa_best_energy_f1",
    "sa_best_observed_f1", "sa_unique_structure_count", "sa_best_energy_hit_rate",
    "best_known_solver", "best_known_energy", "best_known_structure", "best_known_f1",
    "best_observed_f1", "true_positives", "false_positives", "false_negatives",
    "precision", "recall", "exact_match", "runtime_seconds",
]

SA_FIELDS = [
    "variant_id", "sequence_id", "seed", "energy", "structure", "f1_score",
    "true_positives", "false_positives", "false_negatives", "selected_stem_count",
    "is_conflict_free", "runtime_seconds",
]

SUMMARY_FIELDS = [
    "rank", "variant_id", "description", "objective_settings", "sequence_count",
    "success_rate", "control_min_f1", "hairpin_min_f1", "controls_preserved",
    "mixed_mean_best_known_f1", "dev_mixed_18_f1", "micro_precision", "micro_recall",
    "micro_f1", "exact_match_rate", "false_positives", "false_negatives",
    "mean_best_observed_f1", "mean_sa_best_energy_hit_rate",
    "mean_sa_unique_structure_count", "exact_eligible_count",
    "exact_strict_failure_count", "exact_strict_failure_rate", "exact_ambiguity_count",
    "exact_optimal_capture_truncation_count", "mean_qubo_variable_count",
    "mean_quadratic_term_count", "mean_runtime_seconds", "run_dir",
]

DELTA_FIELDS = [
    "variant_id", "sequence_id", "category", "baseline_best_known_f1",
    "variant_best_known_f1", "delta_best_known_f1", "baseline_best_observed_f1",
    "variant_best_observed_f1", "delta_best_observed_f1", "baseline_false_positives",
    "variant_false_positives", "delta_false_positives", "baseline_false_negatives",
    "variant_false_negatives", "delta_false_negatives", "baseline_sa_hit_rate",
    "variant_sa_hit_rate", "delta_sa_hit_rate", "baseline_unique_structures",
    "variant_unique_structures", "delta_unique_structures", "baseline_qubo_variables",
    "variant_qubo_variables", "delta_qubo_variables", "baseline_quadratic_terms",
    "variant_quadratic_terms", "delta_quadratic_terms", "baseline_runtime_seconds",
    "variant_runtime_seconds", "delta_runtime_seconds",
]


def _resolve(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else REPO_ROOT / value


def _safe_id(raw: str | None, prefix: str) -> str:
    candidate = raw or datetime.now(timezone.utc).strftime(f"{prefix}_%Y%m%dT%H%M%SZ")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate).strip("._")
    if not cleaned:
        raise ValueError("Run identifier must contain a letter or number.")
    return cleaned


def _load_yaml(path: Path) -> dict[str, Any]:
    import yaml  # type: ignore

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    import yaml  # type: ignore

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def _number(value: Any, default: float = 0.0) -> float:
    if value in (None, ""):
        return default
    return float(value)


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config["budget"] = dict(DEFAULT_CONFIG["budget"])
    config["selection"] = dict(DEFAULT_CONFIG["selection"])
    config_path = _resolve(path or "configs/phase50B_equal_budget_audit.yaml")
    if config_path.exists():
        loaded = _load_yaml(config_path)
        for key, value in loaded.items():
            if key in {"budget", "selection"} and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    if not config.get("variants"):
        raise ValueError("The equal-budget audit must define objective variants.")
    config["config_path"] = str(config_path)
    return config


def load_strict(path: str | Path) -> dict[str, Any]:
    strict_path = _resolve(path)
    if not strict_path.exists():
        raise FileNotFoundError(f"Locked Phase 49 config was not found: {strict_path}")
    data = _load_yaml(strict_path)
    data["strict_config_path"] = str(strict_path)
    return data


def load_development_dataset(path: str | Path) -> list[dict[str, str]]:
    rows = _read_csv(_resolve(path))
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        if str(row.get("split", "")).strip().lower() != "development":
            continue
        sequence_id = str(row.get("sequence_id", "")).strip()
        if not sequence_id or sequence_id in seen:
            raise ValueError(f"Missing or duplicate development sequence_id: {sequence_id}")
        seen.add(sequence_id)
        result.append({
            "sequence_id": sequence_id,
            "split": "development",
            "category": str(row.get("category", "unknown")).strip() or "unknown",
            "source_type": str(row.get("source_type", "synthetic")).strip() or "synthetic",
            "sequence": str(row.get("sequence", "")).strip().upper().replace("T", "U"),
            "notes": str(row.get("notes", "")).strip(),
        })
    if not result:
        raise ValueError("No development sequences were found.")
    return result


def _metric(reference: str | None, predicted: str | None) -> dict[str, Any] | None:
    if not reference or not predicted or str(predicted).startswith("<invalid:"):
        return None
    return compare_structures(reference, predicted)


def _signature_payload(
    variant: dict[str, Any],
    dataset: list[dict[str, str]],
    strict: dict[str, Any],
    budget: dict[str, Any],
    exact_max_variables: int,
    optimal_structure_capture_limit: int,
) -> dict[str, Any]:
    return {
        "variant": variant,
        "dataset": dataset,
        "strict": {key: value for key, value in strict.items() if key != "strict_config_path"},
        "budget": budget,
        "exact_max_variables": exact_max_variables,
        "optimal_structure_capture_limit": optimal_structure_capture_limit,
    }


def _signature(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _exact_optimum_metrics(reference: str, exact: dict[str, Any]) -> tuple[list[float], str]:
    if exact.get("status") != "success":
        return [], "exact_skipped"
    values: list[float] = []
    for item in exact.get("optimal_structures", []):
        metric = _metric(reference, item.get("structure"))
        if metric is None or metric.get("f1_score") is None:
            # An invalid or undecodable exact optimum is itself an objective
            # failure and must not disappear from the degeneracy audit.
            values.append(0.0)
        else:
            values.append(float(metric["f1_score"]))
    if not values:
        representative = _metric(reference, exact.get("predicted_structure"))
        if representative is not None and representative.get("f1_score") is not None:
            values.append(float(representative["f1_score"]))
    if not values:
        return [], "exact_optimum_unscorable"
    minimum = min(values)
    maximum = max(values)
    if minimum >= 0.999999:
        label = "all_exact_optima_match_reference"
    elif maximum >= 0.999999:
        label = "some_exact_optima_match_reference"
    elif maximum <= 1.0e-12:
        label = "no_exact_optimum_pair_overlap"
    else:
        label = "no_exact_optimum_exact_match"
    return values, label


def _run_sequence(
    row: dict[str, str],
    variant: dict[str, Any],
    strict: dict[str, Any],
    budget: dict[str, Any],
    exact_max_variables: int,
    optimal_structure_capture_limit: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.perf_counter()
    sequence = row["sequence"]
    vienna = run_rnafold(
        sequence,
        executable=str(strict.get("rnafold_executable", "RNAfold")),
        allow_python_fallback=bool(strict.get("allow_vienna_python_fallback", True)),
    )
    if not vienna.get("success"):
        raise RuntimeError(str(vienna.get("error") or "ViennaRNA reference failed."))
    reference = str(vienna["reference_structure"])
    objective = dict(variant.get("objective", {}))
    qubo = build_variant_qubo(sequence, strict, objective)
    exact = solve_variant_qubo_exact(
        sequence,
        qubo,
        max_variables=exact_max_variables,
        collect_optimal_structures=True,
        max_optimal_structures=optimal_structure_capture_limit,
    )
    greedy = solve_variant_qubo_greedy(sequence, qubo)
    exact_metric = _metric(reference, exact.get("predicted_structure"))
    greedy_metric = _metric(reference, greedy.get("predicted_structure"))
    exact_optimal_values, exact_classification = _exact_optimum_metrics(reference, exact)

    sa_rows: list[dict[str, Any]] = []
    candidates: list[tuple[float, int, str, str, dict[str, Any] | None]] = []
    if exact.get("status") == "success" and exact.get("best_energy") is not None:
        candidates.append((float(exact["best_energy"]), 0, "exact", str(exact["predicted_structure"]), exact_metric))
    if greedy.get("best_energy") is not None:
        candidates.append((float(greedy["best_energy"]), 2, "greedy", str(greedy["predicted_structure"]), greedy_metric))

    for seed in [int(value) for value in budget["sa_seeds"]]:
        result = run_fast_sa(
            qubo,
            seed=seed,
            steps=int(budget["sa_steps"]),
            initial_temperature=float(budget["sa_initial_temperature"]),
            final_temperature=float(budget["sa_final_temperature"]),
            cooling_rate=float(budget["sa_cooling_rate"]),
            run_local_refinement=bool(budget["run_local_refinement"]),
        )
        decoded = decode_solution_to_structure(sequence, qubo["stems"], result["refined_solution"])
        structure = str(decoded.get("predicted_structure"))
        metric = _metric(reference, structure)
        energy = float(result["refined_energy"])
        candidates.append((energy, 1, f"sa_seed_{seed}", structure, metric))
        sa_rows.append({
            "variant_id": variant["id"],
            "sequence_id": row["sequence_id"],
            "seed": seed,
            "energy": energy,
            "structure": structure,
            "f1_score": metric.get("f1_score") if metric else None,
            "true_positives": metric.get("true_positives") if metric else None,
            "false_positives": metric.get("false_positives") if metric else None,
            "false_negatives": metric.get("false_negatives") if metric else None,
            "selected_stem_count": decoded.get("selected_stem_count"),
            "is_conflict_free": decoded.get("is_conflict_free"),
            "runtime_seconds": result.get("runtime_seconds"),
        })

    if not candidates:
        raise RuntimeError("No successful exact, greedy, or SA candidate was produced.")
    best_known = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    best_metric = best_known[4]
    observed_f1 = [
        float(item[4]["f1_score"])
        for item in candidates
        if item[4] is not None and item[4].get("f1_score") is not None
    ]
    sa_energies = [float(item["energy"]) for item in sa_rows]
    sa_structures = Counter(str(item["structure"]) for item in sa_rows)
    best_sa_energy = min(sa_energies) if sa_energies else None
    best_sa_rows = [
        item for item in sa_rows
        if best_sa_energy is not None and abs(float(item["energy"]) - best_sa_energy) <= 1.0e-9
    ]
    best_sa_row = min(best_sa_rows, key=lambda item: int(item["seed"])) if best_sa_rows else None
    hit_rate = (
        sum(abs(value - best_sa_energy) <= 1.0e-9 for value in sa_energies) / len(sa_energies)
        if sa_energies and best_sa_energy is not None else None
    )
    return {
        "variant_id": variant["id"],
        "sequence_id": row["sequence_id"],
        "category": row["category"],
        "sequence_length": len(sequence),
        "status": "success",
        "error": None,
        "reference_structure": reference,
        "reference_energy": vienna.get("reference_energy"),
        "qubo_variable_count": qubo["num_variables"],
        "quadratic_term_count": qubo["num_quadratic_terms"],
        "exact_status": exact.get("status"),
        "exact_energy": exact.get("best_energy"),
        "exact_f1": exact_metric.get("f1_score") if exact_metric else None,
        "exact_optimal_assignment_count": exact.get("optimal_assignment_count"),
        "exact_captured_optimal_structure_count": exact.get("captured_optimal_structure_count"),
        "exact_optimal_structures_truncated": exact.get("optimal_structures_truncated"),
        "exact_optimal_min_f1": min(exact_optimal_values) if exact_optimal_values else None,
        "exact_optimal_mean_f1": statistics.fmean(exact_optimal_values) if exact_optimal_values else None,
        "exact_optimal_max_f1": max(exact_optimal_values) if exact_optimal_values else None,
        "exact_optimum_classification": exact_classification,
        "greedy_energy": greedy.get("best_energy"),
        "greedy_f1": greedy_metric.get("f1_score") if greedy_metric else None,
        "sa_best_energy": best_sa_energy,
        "sa_best_energy_f1": best_sa_row.get("f1_score") if best_sa_row else None,
        "sa_best_observed_f1": max((float(item["f1_score"]) for item in sa_rows if item.get("f1_score") is not None), default=None),
        "sa_unique_structure_count": len(sa_structures),
        "sa_best_energy_hit_rate": round(hit_rate, 6) if hit_rate is not None else None,
        "best_known_solver": best_known[2],
        "best_known_energy": best_known[0],
        "best_known_structure": best_known[3],
        "best_known_f1": best_metric.get("f1_score") if best_metric else None,
        "best_observed_f1": max(observed_f1) if observed_f1 else None,
        "true_positives": best_metric.get("true_positives") if best_metric else None,
        "false_positives": best_metric.get("false_positives") if best_metric else None,
        "false_negatives": best_metric.get("false_negatives") if best_metric else None,
        "precision": best_metric.get("precision") if best_metric else None,
        "recall": best_metric.get("recall") if best_metric else None,
        "exact_match": best_metric.get("exact_match") if best_metric else None,
        "runtime_seconds": round(time.perf_counter() - started, 6),
    }, sa_rows


def summarize_variant(
    variant: dict[str, Any],
    rows: list[dict[str, Any]],
    run_dir: Path,
) -> dict[str, Any]:
    successful = [row for row in rows if row.get("status") == "success"]
    mixed = [row for row in successful if row.get("category") == "mixed_composition"]
    controls = [row for row in successful if row.get("category") == "unstructured_control"]
    hairpins = [row for row in successful if row.get("category") in {"designed_hairpin", "wobble_enriched_hairpin"}]
    tp = sum(int(row.get("true_positives") or 0) for row in successful)
    fp = sum(int(row.get("false_positives") or 0) for row in successful)
    fn = sum(int(row.get("false_negatives") or 0) for row in successful)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    micro_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    control_values = [float(row["best_known_f1"]) for row in controls if row.get("best_known_f1") is not None]
    hairpin_values = [float(row["best_known_f1"]) for row in hairpins if row.get("best_known_f1") is not None]
    control_min = min(control_values) if control_values else None
    hairpin_min = min(hairpin_values) if hairpin_values else None
    preserved = (
        (control_min is None or control_min >= 0.999999)
        and (hairpin_min is None or hairpin_min >= 0.999999)
    )
    mixed_18 = next((row for row in successful if row.get("sequence_id") == "dev_mixed_18"), None)
    exact_rows = [row for row in successful if row.get("exact_status") == "success"]
    exact_strict_failures = [
        row for row in exact_rows
        if row.get("exact_optimal_max_f1") is None or float(row["exact_optimal_max_f1"]) < 0.999999
    ]
    exact_ambiguities = [
        row for row in exact_rows
        if row.get("exact_optimal_min_f1") is not None
        and row.get("exact_optimal_max_f1") is not None
        and abs(float(row["exact_optimal_max_f1"]) - float(row["exact_optimal_min_f1"])) > 1.0e-9
    ]
    return {
        "rank": None,
        "variant_id": variant["id"],
        "description": variant.get("description", ""),
        "objective_settings": json.dumps(variant.get("objective", {}), sort_keys=True),
        "sequence_count": len(rows),
        "success_rate": round(len(successful) / len(rows), 6) if rows else 0.0,
        "control_min_f1": round(control_min, 6) if control_min is not None else None,
        "hairpin_min_f1": round(hairpin_min, 6) if hairpin_min is not None else None,
        "controls_preserved": bool(preserved),
        "mixed_mean_best_known_f1": _mean([float(row["best_known_f1"]) for row in mixed if row.get("best_known_f1") is not None]),
        "dev_mixed_18_f1": float(mixed_18["best_known_f1"]) if mixed_18 and mixed_18.get("best_known_f1") is not None else None,
        "micro_precision": round(precision, 6),
        "micro_recall": round(recall, 6),
        "micro_f1": round(micro_f1, 6),
        "exact_match_rate": round(sum(bool(row.get("exact_match")) for row in successful) / len(successful), 6) if successful else 0.0,
        "false_positives": fp,
        "false_negatives": fn,
        "mean_best_observed_f1": _mean([float(row["best_observed_f1"]) for row in successful if row.get("best_observed_f1") is not None]),
        "mean_sa_best_energy_hit_rate": _mean([float(row["sa_best_energy_hit_rate"]) for row in successful if row.get("sa_best_energy_hit_rate") is not None]),
        "mean_sa_unique_structure_count": _mean([float(row["sa_unique_structure_count"]) for row in successful if row.get("sa_unique_structure_count") is not None]),
        "exact_eligible_count": len(exact_rows),
        "exact_strict_failure_count": len(exact_strict_failures),
        "exact_strict_failure_rate": round(len(exact_strict_failures) / len(exact_rows), 6) if exact_rows else None,
        "exact_ambiguity_count": len(exact_ambiguities),
        "exact_optimal_capture_truncation_count": sum(bool(row.get("exact_optimal_structures_truncated")) for row in exact_rows),
        "mean_qubo_variable_count": _mean([float(row["qubo_variable_count"]) for row in successful]),
        "mean_quadratic_term_count": _mean([float(row["quadratic_term_count"]) for row in successful]),
        "mean_runtime_seconds": _mean([float(row["runtime_seconds"]) for row in successful]),
        "run_dir": str(run_dir),
    }


def ranking_key(summary: dict[str, Any]) -> tuple[Any, ...]:
    """Equal-budget ranking with an exact-objective guardrail."""

    exact_failure_rate = summary.get("exact_strict_failure_rate")
    return (
        -float(summary.get("success_rate") or 0.0),
        -int(bool(summary.get("controls_preserved"))),
        -float(summary.get("mixed_mean_best_known_f1") or 0.0),
        -float(summary.get("dev_mixed_18_f1") or 0.0),
        -float(summary.get("micro_f1") or 0.0),
        float(exact_failure_rate) if exact_failure_rate is not None else 1.0,
        int(summary.get("exact_ambiguity_count") or 0),
        int(summary.get("false_positives") or 0),
        int(summary.get("false_negatives") or 0),
        -float(summary.get("mean_sa_best_energy_hit_rate") or 0.0),
        float(summary.get("mean_sa_unique_structure_count") or 0.0),
        float(summary.get("mean_qubo_variable_count") or 0.0),
        float(summary.get("mean_runtime_seconds") or 0.0),
        str(summary.get("variant_id")),
    )


def _run_variant(
    variant: dict[str, Any],
    dataset: list[dict[str, str]],
    strict: dict[str, Any],
    budget: dict[str, Any],
    exact_max_variables: int,
    optimal_structure_capture_limit: int,
    run_dir: Path,
    resume: bool,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    signature_payload = _signature_payload(
        variant, dataset, strict, budget, exact_max_variables, optimal_structure_capture_limit
    )
    expected_signature = _signature(signature_payload)
    summary_path = run_dir / "config_summary.json"
    signature_path = run_dir / "run_signature.json"
    if resume and summary_path.exists():
        if not signature_path.exists():
            raise RuntimeError(
                f"Refusing unsafe resume for {variant['id']}: run_signature.json is missing."
            )
        existing = json.loads(signature_path.read_text(encoding="utf-8"))
        if existing.get("sha256") != expected_signature:
            raise RuntimeError(
                f"Refusing stale resume for {variant['id']}: the dataset, objective, "
                "strict configuration, or solver budget changed. Use a new run ID."
            )
        print(f"[RESUME] {variant['id']}")
        rows = _read_csv(run_dir / "sequence_summary.csv")
        return json.loads(summary_path.read_text(encoding="utf-8")), rows

    run_dir.mkdir(parents=True, exist_ok=True)
    sequence_rows: list[dict[str, Any]] = []
    sa_rows: list[dict[str, Any]] = []
    for index, row in enumerate(dataset, start=1):
        print(f"  [{index}/{len(dataset)}] {row['sequence_id']} ({len(row['sequence'])} nt)")
        try:
            sequence_row, sequence_sa = _run_sequence(
                row,
                variant,
                strict,
                budget,
                exact_max_variables,
                optimal_structure_capture_limit,
            )
            sequence_rows.append(sequence_row)
            sa_rows.extend(sequence_sa)
        except Exception as exc:
            sequence_rows.append({
                "variant_id": variant["id"],
                "sequence_id": row["sequence_id"],
                "category": row["category"],
                "sequence_length": len(row["sequence"]),
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
    summary = summarize_variant(variant, sequence_rows, run_dir)
    _write_csv(run_dir / "sequence_summary.csv", sequence_rows, SEQUENCE_FIELDS)
    _write_csv(run_dir / "sa_runs.csv", sa_rows, SA_FIELDS)
    _write_json(summary_path, summary)
    _write_json(signature_path, {"sha256": expected_signature, "payload": signature_payload})
    _write_yaml(run_dir / "objective_variant.yaml", variant)
    return summary, sequence_rows


def _rank(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(summaries, key=ranking_key)
    for index, summary in enumerate(ranked, start=1):
        summary["rank"] = index
    return ranked


def _delta(current: Any, baseline: Any) -> float | None:
    if current in (None, "") or baseline in (None, ""):
        return None
    return round(float(current) - float(baseline), 6)


def paired_deltas(
    baseline_rows: list[dict[str, Any]],
    variant_rows: list[dict[str, Any]],
    variant_id: str,
) -> list[dict[str, Any]]:
    baseline = {str(row["sequence_id"]): row for row in baseline_rows}
    result: list[dict[str, Any]] = []
    for row in variant_rows:
        sequence_id = str(row["sequence_id"])
        base = baseline.get(sequence_id)
        if base is None:
            continue
        result.append({
            "variant_id": variant_id,
            "sequence_id": sequence_id,
            "category": row.get("category"),
            "baseline_best_known_f1": base.get("best_known_f1"),
            "variant_best_known_f1": row.get("best_known_f1"),
            "delta_best_known_f1": _delta(row.get("best_known_f1"), base.get("best_known_f1")),
            "baseline_best_observed_f1": base.get("best_observed_f1"),
            "variant_best_observed_f1": row.get("best_observed_f1"),
            "delta_best_observed_f1": _delta(row.get("best_observed_f1"), base.get("best_observed_f1")),
            "baseline_false_positives": base.get("false_positives"),
            "variant_false_positives": row.get("false_positives"),
            "delta_false_positives": _delta(row.get("false_positives"), base.get("false_positives")),
            "baseline_false_negatives": base.get("false_negatives"),
            "variant_false_negatives": row.get("false_negatives"),
            "delta_false_negatives": _delta(row.get("false_negatives"), base.get("false_negatives")),
            "baseline_sa_hit_rate": base.get("sa_best_energy_hit_rate"),
            "variant_sa_hit_rate": row.get("sa_best_energy_hit_rate"),
            "delta_sa_hit_rate": _delta(row.get("sa_best_energy_hit_rate"), base.get("sa_best_energy_hit_rate")),
            "baseline_unique_structures": base.get("sa_unique_structure_count"),
            "variant_unique_structures": row.get("sa_unique_structure_count"),
            "delta_unique_structures": _delta(row.get("sa_unique_structure_count"), base.get("sa_unique_structure_count")),
            "baseline_qubo_variables": base.get("qubo_variable_count"),
            "variant_qubo_variables": row.get("qubo_variable_count"),
            "delta_qubo_variables": _delta(row.get("qubo_variable_count"), base.get("qubo_variable_count")),
            "baseline_quadratic_terms": base.get("quadratic_term_count"),
            "variant_quadratic_terms": row.get("quadratic_term_count"),
            "delta_quadratic_terms": _delta(row.get("quadratic_term_count"), base.get("quadratic_term_count")),
            "baseline_runtime_seconds": base.get("runtime_seconds"),
            "variant_runtime_seconds": row.get("runtime_seconds"),
            "delta_runtime_seconds": _delta(row.get("runtime_seconds"), base.get("runtime_seconds")),
        })
    return result


def selection_decision(
    ranked: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    selection = dict(config["selection"])
    baseline_id = str(selection["baseline_variant_id"])
    baseline = next((row for row in ranked if row["variant_id"] == baseline_id), None)
    if baseline is None:
        raise ValueError(f"Baseline variant {baseline_id!r} was not included in the audit.")
    selected = ranked[0]
    margin = float(selection.get("micro_f1_noninferiority_margin", 0.03))
    exact_margin = float(selection.get("exact_failure_rate_noninferiority_margin", 0.0))
    reasons: list[str] = []
    checks = {
        "all_runs_successful": float(selected.get("success_rate") or 0.0) >= 0.999999,
        "controls_preserved": bool(selected.get("controls_preserved")),
        "mixed_f1_not_worse_than_baseline": _number(selected.get("mixed_mean_best_known_f1")) >= _number(baseline.get("mixed_mean_best_known_f1")) - 1.0e-12,
        "dev_mixed_18_not_worse_than_baseline": _number(selected.get("dev_mixed_18_f1")) >= _number(baseline.get("dev_mixed_18_f1")) - 1.0e-12,
        "micro_f1_within_noninferiority_margin": _number(selected.get("micro_f1")) >= _number(baseline.get("micro_f1")) - margin - 1.0e-12,
        "exact_failure_rate_not_worse_than_baseline": _number(selected.get("exact_strict_failure_rate"), 1.0) <= _number(baseline.get("exact_strict_failure_rate"), 1.0) + exact_margin + 1.0e-12,
        "exact_optimal_capture_complete": int(selected.get("exact_optimal_capture_truncation_count") or 0) == 0,
    }
    for name, passed in checks.items():
        if not passed:
            reasons.append(name)
    lock_recommended = all(checks.values())
    return {
        "selected_variant_id": selected["variant_id"],
        "baseline_variant_id": baseline_id,
        "lock_recommended": lock_recommended,
        "failed_guardrails": reasons,
        "guardrail_checks": checks,
        "micro_f1_noninferiority_margin": margin,
        "exact_failure_rate_noninferiority_margin": exact_margin,
        "selected_summary": selected,
        "baseline_summary": baseline,
        "phase49_validation_used": False,
        "phase50_final_test_used": False,
    }


def _report(run_id: str, ranked: list[dict[str, Any]], decision: dict[str, Any]) -> str:
    selected = decision["selected_summary"]
    baseline = decision["baseline_summary"]
    lines = [
        "# Phase 50B.1 Equal-Budget Selection Audit", "",
        f"- Run ID: `{run_id}`",
        "- Development sequences only: True",
        "- Equal SA seeds per variant: 12 (unless overridden for smoke verification)",
        "- Equal SA steps per seed: 6000 (unless overridden for smoke verification)",
        f"- Selected variant: `{selected['variant_id']}`",
        f"- Formal lock recommended: {decision['lock_recommended']}",
        "- Phase 50 final-test used: False", "",
        "## Methodological fixes", "",
        "- Baseline and both candidate objectives use the same solver budget.",
        "- Exact-optimum degeneracy is captured and scored instead of silently using only the first minimum-energy assignment.",
        "- Resume requires a matching SHA-256 run signature.",
        "- Per-sequence paired deltas are written against the frozen baseline.", "",
        "## Equal-budget comparison", "",
        "| Rank | Variant | Mixed mean F1 | dev_mixed_18 F1 | Micro F1 | Exact failure rate | SA hit rate | Mean variables |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in ranked:
        lines.append(
            f"| {row['rank']} | `{row['variant_id']}` | {row.get('mixed_mean_best_known_f1')} | "
            f"{row.get('dev_mixed_18_f1')} | {row.get('micro_f1')} | "
            f"{row.get('exact_strict_failure_rate')} | {row.get('mean_sa_best_energy_hit_rate')} | "
            f"{row.get('mean_qubo_variable_count')} |"
        )
    lines.extend([
        "", "## Baseline comparison", "",
        f"- Baseline mixed mean F1: {baseline.get('mixed_mean_best_known_f1')}",
        f"- Selected mixed mean F1: {selected.get('mixed_mean_best_known_f1')}",
        f"- Baseline micro F1: {baseline.get('micro_f1')}",
        f"- Selected micro F1: {selected.get('micro_f1')}",
        f"- Baseline exact strict-failure rate: {baseline.get('exact_strict_failure_rate')}",
        f"- Selected exact strict-failure rate: {selected.get('exact_strict_failure_rate')}",
        "", "## Lock guardrails", "",
    ])
    for name, passed in decision["guardrail_checks"].items():
        lines.append(f"- {name}: {passed}")
    lines.extend([
        "", "## Frozen-data rule", "",
        "The Phase 50 `final_test` split remains unused. Run it only after this audit recommends a lock and the selected configuration is committed and tagged.",
        "", "## Interpretation boundary", "",
        "This is a small synthetic development audit against ViennaRNA MFE references. It does not establish biological validation or quantum advantage.",
        "", "## Reproducibility files", "",
        "- `dataset_snapshot.csv`",
        "- `effective_audit_config.yaml`",
        "- `effective_strict_config.yaml`",
        "- `equal_budget_summary.csv`",
        "- `paired_sequence_deltas.csv`",
        "- `selection_decision.json`",
        "- `provisional_selected_objective_config.yaml`",
        "- `locked_objective_config.yaml` when all guardrails pass",
        "- per-variant `sequence_summary.csv`, `sa_runs.csv`, and `run_signature.json`",
        "",
    ])
    return "\n".join(lines)


def run_equal_budget_audit(
    run_id: str | None = None,
    config_path: str | Path | None = None,
    sequence_limit: int | None = None,
    seed_limit: int | None = None,
    steps: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    strict = load_strict(config["strict_config_path"])
    dataset = load_development_dataset(config["dataset_path"])
    if sequence_limit is not None:
        dataset = dataset[: int(sequence_limit)]
    budget = dict(config["budget"])
    if seed_limit is not None:
        budget["sa_seeds"] = list(budget["sa_seeds"])[: int(seed_limit)]
    if steps is not None:
        budget["sa_steps"] = int(steps)
    variants = [dict(value) for value in config["variants"]]
    identifiers = [str(value.get("id", "")) for value in variants]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("Each audit variant must have a unique non-empty id.")
    required = {"baseline_sum", "short2_penalty_3", "min_stem_length_3"}
    if set(identifiers) != required:
        raise ValueError(
            "The equal-budget audit must contain exactly baseline_sum, "
            "short2_penalty_3, and min_stem_length_3."
        )

    safe_run_id = _safe_id(run_id, "phase50B1_equal_budget")
    output_dir = _resolve(config["output_root"]) / safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "dataset_snapshot.csv", dataset, [
        "sequence_id", "split", "category", "source_type", "sequence", "notes"
    ])
    effective_config = dict(config)
    effective_config["budget"] = budget
    _write_yaml(output_dir / "effective_audit_config.yaml", effective_config)
    _write_yaml(output_dir / "effective_strict_config.yaml", strict)

    summaries: list[dict[str, Any]] = []
    rows_by_variant: dict[str, list[dict[str, Any]]] = {}
    for index, variant in enumerate(variants, start=1):
        print(f"[AUDIT {index}/{len(variants)}] {variant['id']}")
        summary, rows = _run_variant(
            variant,
            dataset,
            strict,
            budget,
            int(config["exact_max_variables"]),
            int(config["optimal_structure_capture_limit"]),
            output_dir / "variants" / variant["id"],
            bool(config.get("resume", True)),
        )
        summaries.append(summary)
        rows_by_variant[variant["id"]] = rows

    ranked = _rank(summaries)
    _write_csv(output_dir / "equal_budget_summary.csv", ranked, SUMMARY_FIELDS)
    baseline_id = str(config["selection"]["baseline_variant_id"])
    delta_rows: list[dict[str, Any]] = []
    for variant_id, rows in rows_by_variant.items():
        if variant_id == baseline_id:
            continue
        delta_rows.extend(paired_deltas(rows_by_variant[baseline_id], rows, variant_id))
    _write_csv(output_dir / "paired_sequence_deltas.csv", delta_rows, DELTA_FIELDS)

    decision = selection_decision(ranked, config)
    _write_json(output_dir / "selection_decision.json", decision)
    selected_variant = next(value for value in variants if value["id"] == decision["selected_variant_id"])
    provisional = {
        **{key: value for key, value in strict.items() if key != "strict_config_path"},
        "phase50B_objective_variant_id": selected_variant["id"],
        "phase50B_objective": selected_variant.get("objective", {}),
        "phase50B1_equal_budget_audit_run_id": safe_run_id,
        "phase50B1_lock_recommended": bool(decision["lock_recommended"]),
        "notes": (
            "Selected on the Phase 50 development split under an equal solver budget. "
            "The Phase 50 final_test split remains frozen."
        ),
    }
    _write_yaml(output_dir / "provisional_selected_objective_config.yaml", provisional)
    locked_path: Path | None = None
    if decision["lock_recommended"]:
        locked_path = output_dir / "locked_objective_config.yaml"
        _write_yaml(locked_path, provisional)
    (output_dir / "equal_budget_audit_report.md").write_text(
        _report(safe_run_id, ranked, decision), encoding="utf-8"
    )
    print(f"[OK] Equal-budget audit saved to: {output_dir}")
    print(f"[OK] Selected variant: {decision['selected_variant_id']}")
    print(f"[OK] Lock recommended: {decision['lock_recommended']}")
    print("[OK] Final-test split used: False")
    return {
        "output_dir": str(output_dir),
        "ranked": ranked,
        "decision": decision,
        "locked_config": str(locked_path) if locked_path else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 50B.1 equal-budget development-only selection audit."
    )
    parser.add_argument("--run-id")
    parser.add_argument("--config", default="configs/phase50B_equal_budget_audit.yaml")
    parser.add_argument("--sequence-limit", type=int)
    parser.add_argument("--seed-limit", type=int)
    parser.add_argument("--steps", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_equal_budget_audit(
            run_id=args.run_id,
            config_path=args.config,
            sequence_limit=args.sequence_limit,
            seed_limit=args.seed_limit,
            steps=args.steps,
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
