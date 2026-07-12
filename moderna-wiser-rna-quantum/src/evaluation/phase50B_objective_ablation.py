"""Phase 50B controlled objective-ablation runner.

This phase changes one linear stem-scoring assumption at a time while keeping
Phase 49 conflict penalties frozen. It uses only the Phase 50 development split.
The Phase 50 final-test split is intentionally blocked in this module.
"""

from __future__ import annotations

import argparse
import csv
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
    "output_root": "results/phase50B_objective_ablation",
    "resume": True,
    "top_k": 3,
    "exact_max_variables": 20,
    "screen": {
        "sa_seeds": [3, 7, 11, 19],
        "sa_steps": 2500,
        "sa_initial_temperature": 10.0,
        "sa_final_temperature": 0.01,
        "sa_cooling_rate": 0.995,
        "run_local_refinement": True,
    },
    "confirmation": {
        "sa_seeds": [3, 7, 11, 19, 23, 29, 31, 37, 41, 43, 47, 53],
        "sa_steps": 6000,
        "sa_initial_temperature": 10.0,
        "sa_final_temperature": 0.01,
        "sa_cooling_rate": 0.995,
        "run_local_refinement": True,
    },
    "variants": [],
}

SEQUENCE_FIELDS = [
    "variant_id", "stage", "sequence_id", "category", "sequence_length",
    "status", "error", "reference_structure", "reference_energy",
    "qubo_variable_count", "quadratic_term_count", "exact_status",
    "exact_energy", "exact_f1", "greedy_energy", "greedy_f1",
    "sa_best_energy", "sa_best_energy_f1", "sa_best_observed_f1",
    "sa_unique_structure_count", "sa_best_energy_hit_rate",
    "best_known_solver", "best_known_energy", "best_known_structure",
    "best_known_f1", "best_observed_f1", "true_positives",
    "false_positives", "false_negatives", "precision", "recall",
    "exact_match", "runtime_seconds",
]

SA_FIELDS = [
    "variant_id", "stage", "sequence_id", "seed", "energy", "structure",
    "f1_score", "true_positives", "false_positives", "false_negatives",
    "selected_stem_count", "is_conflict_free", "runtime_seconds",
]

SUMMARY_FIELDS = [
    "rank", "variant_id", "stage", "description", "objective_settings",
    "sequence_count", "success_rate", "control_min_f1", "hairpin_min_f1",
    "controls_preserved", "mixed_mean_best_known_f1", "dev_mixed_18_f1",
    "micro_precision", "micro_recall", "micro_f1", "exact_match_rate",
    "false_positives", "false_negatives", "mean_best_observed_f1",
    "mean_sa_best_energy_hit_rate", "mean_sa_unique_structure_count",
    "small_exact_objective_failure_count", "mean_qubo_variable_count",
    "mean_quadratic_term_count", "mean_runtime_seconds", "run_dir",
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


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config["screen"] = dict(DEFAULT_CONFIG["screen"])
    config["confirmation"] = dict(DEFAULT_CONFIG["confirmation"])
    config_path = _resolve(path or "configs/phase50B_objective_ablation.yaml")
    if config_path.exists():
        loaded = _load_yaml(config_path)
        for key, value in loaded.items():
            if key in {"screen", "confirmation"} and isinstance(value, dict):
                config[key].update(value)
            else:
                config[key] = value
    if not config.get("variants"):
        raise ValueError("Phase 50B config must define at least one objective variant.")
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
    result = []
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
    if not reference or not predicted:
        return None
    return compare_structures(reference, predicted)


def _mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def _run_sequence(
    row: dict[str, str],
    variant: dict[str, Any],
    strict: dict[str, Any],
    stage_name: str,
    stage_config: dict[str, Any],
    exact_max_variables: int,
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
    exact = solve_variant_qubo_exact(sequence, qubo, max_variables=exact_max_variables)
    greedy = solve_variant_qubo_greedy(sequence, qubo)
    exact_metric = _metric(reference, exact.get("predicted_structure"))
    greedy_metric = _metric(reference, greedy.get("predicted_structure"))

    sa_rows: list[dict[str, Any]] = []
    candidates: list[tuple[float, int, str, str, dict[str, Any] | None]] = []
    if exact.get("status") == "success" and exact.get("best_energy") is not None:
        candidates.append((float(exact["best_energy"]), 0, "exact", str(exact["predicted_structure"]), exact_metric))
    if greedy.get("best_energy") is not None:
        candidates.append((float(greedy["best_energy"]), 2, "greedy", str(greedy["predicted_structure"]), greedy_metric))

    for seed in [int(value) for value in stage_config["sa_seeds"]]:
        result = run_fast_sa(
            qubo,
            seed=seed,
            steps=int(stage_config["sa_steps"]),
            initial_temperature=float(stage_config["sa_initial_temperature"]),
            final_temperature=float(stage_config["sa_final_temperature"]),
            cooling_rate=float(stage_config["sa_cooling_rate"]),
            run_local_refinement=bool(stage_config["run_local_refinement"]),
        )
        decoded = decode_solution_to_structure(sequence, qubo["stems"], result["refined_solution"])
        structure = str(decoded.get("predicted_structure"))
        metric = _metric(reference, structure)
        energy = float(result["refined_energy"])
        candidates.append((energy, 1, f"sa_seed_{seed}", structure, metric))
        sa_rows.append({
            "variant_id": variant["id"],
            "stage": stage_name,
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
    best_sa_rows = [item for item in sa_rows if best_sa_energy is not None and abs(float(item["energy"]) - best_sa_energy) <= 1.0e-9]
    best_sa_row = min(best_sa_rows, key=lambda item: int(item["seed"])) if best_sa_rows else None
    hit_rate = (
        sum(abs(value - best_sa_energy) <= 1.0e-9 for value in sa_energies) / len(sa_energies)
        if sa_energies and best_sa_energy is not None else None
    )
    return {
        "variant_id": variant["id"],
        "stage": stage_name,
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
    stage: str,
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
    exact_failures = sum(
        1 for row in successful
        if row.get("exact_status") == "success"
        and row.get("exact_f1") is not None
        and float(row["exact_f1"]) < 0.999999
    )
    return {
        "rank": None,
        "variant_id": variant["id"],
        "stage": stage,
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
        "small_exact_objective_failure_count": exact_failures,
        "mean_qubo_variable_count": _mean([float(row["qubo_variable_count"]) for row in successful]),
        "mean_quadratic_term_count": _mean([float(row["quadratic_term_count"]) for row in successful]),
        "mean_runtime_seconds": _mean([float(row["runtime_seconds"]) for row in successful]),
        "run_dir": str(run_dir),
    }


def ranking_key(summary: dict[str, Any]) -> tuple[Any, ...]:
    """Lexicographic ranking that protects controls before optimizing mixed cases."""

    return (
        -float(summary.get("success_rate") or 0.0),
        -int(bool(summary.get("controls_preserved"))),
        -float(summary.get("mixed_mean_best_known_f1") or 0.0),
        -float(summary.get("dev_mixed_18_f1") or 0.0),
        -float(summary.get("micro_f1") or 0.0),
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
    stage_name: str,
    stage_config: dict[str, Any],
    exact_max_variables: int,
    run_dir: Path,
    resume: bool,
) -> dict[str, Any]:
    summary_path = run_dir / "config_summary.json"
    if resume and summary_path.exists():
        print(f"[RESUME] {stage_name} {variant['id']}")
        return json.loads(summary_path.read_text(encoding="utf-8"))
    run_dir.mkdir(parents=True, exist_ok=True)
    sequence_rows: list[dict[str, Any]] = []
    sa_rows: list[dict[str, Any]] = []
    for index, row in enumerate(dataset, start=1):
        print(f"  [{index}/{len(dataset)}] {row['sequence_id']} ({len(row['sequence'])} nt)")
        try:
            sequence_row, sequence_sa = _run_sequence(
                row, variant, strict, stage_name, stage_config, exact_max_variables
            )
            sequence_rows.append(sequence_row)
            sa_rows.extend(sequence_sa)
        except Exception as exc:
            sequence_rows.append({
                "variant_id": variant["id"], "stage": stage_name,
                "sequence_id": row["sequence_id"], "category": row["category"],
                "sequence_length": len(row["sequence"]), "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
    summary = summarize_variant(variant, stage_name, sequence_rows, run_dir)
    _write_csv(run_dir / "sequence_summary.csv", sequence_rows, SEQUENCE_FIELDS)
    _write_csv(run_dir / "sa_runs.csv", sa_rows, SA_FIELDS)
    _write_json(summary_path, summary)
    _write_yaml(run_dir / "objective_variant.yaml", variant)
    return summary


def _rank(summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(summaries, key=ranking_key)
    for index, summary in enumerate(ranked, start=1):
        summary["rank"] = index
    return ranked


def _report(
    run_id: str,
    screen: list[dict[str, Any]],
    confirmation: list[dict[str, Any]],
    selected: dict[str, Any],
    output_dir: Path,
) -> str:
    baseline = next((row for row in confirmation if row["variant_id"] == "baseline_sum"), None)
    if baseline is None:
        baseline = next((row for row in screen if row["variant_id"] == "baseline_sum"), None)
    lines = [
        "# Phase 50B Objective Ablation Report", "",
        f"- Run ID: `{run_id}`",
        f"- Screened variants: {len(screen)}",
        f"- Confirmed variants: {len(confirmation)}",
        f"- Selected variant: `{selected['variant_id']}`",
        f"- Development mixed mean F1: {selected.get('mixed_mean_best_known_f1')}",
        f"- Development `dev_mixed_18` F1: {selected.get('dev_mixed_18_f1')}",
        f"- Controls preserved: {selected.get('controls_preserved')}",
        "",
        "## Selection rule", "",
        "Variants are ranked by successful-run rate, preservation of the simple controls, mixed-composition mean F1, exact-solvable `dev_mixed_18` F1, micro F1, false-positive count, false-negative count, solver stability, QUBO size, and runtime.",
        "",
        "## Frozen-data rule", "",
        "Only the Phase 50 development split was used. The Phase 50 `final_test` split remains unused and must not be evaluated until the objective configuration is reviewed and locked.",
        "",
        "## Interpretation boundary", "",
        "These experiments measure agreement with ViennaRNA MFE references on a small synthetic development dataset. They do not establish biological generalization or quantum advantage.",
    ]
    if baseline:
        lines.extend([
            "", "## Baseline comparison", "",
            f"- Baseline mixed mean F1: {baseline.get('mixed_mean_best_known_f1')}",
            f"- Selected mixed mean F1: {selected.get('mixed_mean_best_known_f1')}",
            f"- Baseline `dev_mixed_18` F1: {baseline.get('dev_mixed_18_f1')}",
            f"- Selected `dev_mixed_18` F1: {selected.get('dev_mixed_18_f1')}",
        ])
    lines.extend([
        "", "## Reproducibility files", "",
        "- `dataset_snapshot.csv`",
        "- `effective_ablation_config.yaml`",
        "- `effective_strict_config.yaml`",
        "- `screen_summary.csv`",
        "- `confirmation_summary.csv`",
        "- `selected_objective.json`",
        "- `selected_objective_config.yaml`",
        "- per-variant `sequence_summary.csv` and `sa_runs.csv` files",
        "",
    ])
    return "\n".join(lines)


def run_ablation(
    run_id: str | None = None,
    config_path: str | Path | None = None,
    sequence_limit: int | None = None,
    screen_seed_limit: int | None = None,
    confirmation_seed_limit: int | None = None,
    screen_steps: int | None = None,
    confirmation_steps: int | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    config = load_config(config_path)
    strict = load_strict(config["strict_config_path"])
    dataset = load_development_dataset(config["dataset_path"])
    if sequence_limit is not None:
        dataset = dataset[: int(sequence_limit)]
    screen_config = dict(config["screen"])
    confirmation_config = dict(config["confirmation"])
    if screen_seed_limit is not None:
        screen_config["sa_seeds"] = list(screen_config["sa_seeds"])[:screen_seed_limit]
    if confirmation_seed_limit is not None:
        confirmation_config["sa_seeds"] = list(confirmation_config["sa_seeds"])[:confirmation_seed_limit]
    if screen_steps is not None:
        screen_config["sa_steps"] = int(screen_steps)
    if confirmation_steps is not None:
        confirmation_config["sa_steps"] = int(confirmation_steps)
    selected_top_k = int(top_k if top_k is not None else config["top_k"])
    safe_run_id = _safe_id(run_id, "phase50B_ablation")
    output_dir = _resolve(config["output_root"]) / safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "dataset_snapshot.csv", dataset, ["sequence_id", "split", "category", "source_type", "sequence", "notes"])
    effective_config = dict(config)
    effective_config["screen"] = screen_config
    effective_config["confirmation"] = confirmation_config
    effective_config["top_k"] = selected_top_k
    _write_yaml(output_dir / "effective_ablation_config.yaml", effective_config)
    _write_yaml(output_dir / "effective_strict_config.yaml", strict)

    variants = [dict(value) for value in config["variants"]]
    identifiers = [str(value.get("id", "")) for value in variants]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("Each objective variant must have a unique non-empty id.")

    screen_summaries = []
    for index, variant in enumerate(variants, start=1):
        print(f"[SCREEN {index}/{len(variants)}] {variant['id']}")
        screen_summaries.append(_run_variant(
            variant, dataset, strict, "screen", screen_config,
            int(config["exact_max_variables"]),
            output_dir / "screen" / variant["id"],
            bool(config.get("resume", True)),
        ))
    ranked_screen = _rank(screen_summaries)
    _write_csv(output_dir / "screen_summary.csv", ranked_screen, SUMMARY_FIELDS)

    top_variants = []
    by_id = {variant["id"]: variant for variant in variants}
    for summary in ranked_screen[: max(1, selected_top_k)]:
        top_variants.append(by_id[summary["variant_id"]])
    confirmation_summaries = []
    for index, variant in enumerate(top_variants, start=1):
        print(f"[CONFIRM {index}/{len(top_variants)}] {variant['id']}")
        confirmation_summaries.append(_run_variant(
            variant, dataset, strict, "confirmation", confirmation_config,
            int(config["exact_max_variables"]),
            output_dir / "confirmation" / variant["id"],
            bool(config.get("resume", True)),
        ))
    ranked_confirmation = _rank(confirmation_summaries)
    _write_csv(output_dir / "confirmation_summary.csv", ranked_confirmation, SUMMARY_FIELDS)
    selected_summary = ranked_confirmation[0]
    selected_variant = by_id[selected_summary["variant_id"]]
    selected_payload = {
        "selected_variant_id": selected_variant["id"],
        "selected_description": selected_variant.get("description", ""),
        "selected_objective": selected_variant.get("objective", {}),
        "selected_summary": selected_summary,
        "ranking_rule": [
            "success_rate", "controls_preserved", "mixed_mean_best_known_f1",
            "dev_mixed_18_f1", "micro_f1", "lower_false_positives",
            "lower_false_negatives", "solver_stability", "lower_qubo_size",
            "lower_runtime",
        ],
        "phase49_validation_used": False,
        "phase50_final_test_used": False,
    }
    _write_json(output_dir / "selected_objective.json", selected_payload)
    locked = {
        **{key: value for key, value in strict.items() if key != "strict_config_path"},
        "phase50B_objective_variant_id": selected_variant["id"],
        "phase50B_objective": selected_variant.get("objective", {}),
        "notes": (
            "Phase 50B objective selected on the development split only. "
            "The Phase 50 final_test split remains frozen."
        ),
    }
    _write_yaml(output_dir / "selected_objective_config.yaml", locked)
    (output_dir / "ablation_report.md").write_text(
        _report(safe_run_id, ranked_screen, ranked_confirmation, selected_summary, output_dir),
        encoding="utf-8",
    )
    print(f"[OK] Phase 50B ablation saved to: {output_dir}")
    print(f"[OK] Selected variant: {selected_variant['id']}")
    print(f"[OK] Final-test split used: False")
    return {
        "output_dir": str(output_dir),
        "selected_variant": selected_variant,
        "selected_summary": selected_summary,
        "screen": ranked_screen,
        "confirmation": ranked_confirmation,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 50B controlled objective ablations on the development split only.")
    parser.add_argument("--run-id")
    parser.add_argument("--config", default="configs/phase50B_objective_ablation.yaml")
    parser.add_argument("--sequence-limit", type=int)
    parser.add_argument("--screen-seed-limit", type=int)
    parser.add_argument("--confirmation-seed-limit", type=int)
    parser.add_argument("--screen-steps", type=int)
    parser.add_argument("--confirmation-steps", type=int)
    parser.add_argument("--top-k", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_ablation(
            run_id=args.run_id,
            config_path=args.config,
            sequence_limit=args.sequence_limit,
            screen_seed_limit=args.screen_seed_limit,
            confirmation_seed_limit=args.confirmation_seed_limit,
            screen_steps=args.screen_steps,
            confirmation_steps=args.confirmation_steps,
            top_k=args.top_k,
        )
        return 0
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
