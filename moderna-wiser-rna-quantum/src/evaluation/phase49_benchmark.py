"""Phase 49 multi-sequence classical benchmark runner.

The runner reuses the verified Phase 48 one-sequence pipeline and aggregates its
saved outputs. It intentionally keeps calibration and validation splits explicit.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence
from src.evaluation.phase49_metrics import (
    length_bucket,
    summarize_benchmark_rows,
    summarize_groups,
    summarize_scaling,
)
from src.evaluation.strict_classical_pipeline import run_pipeline

DEFAULT_BENCHMARK_CONFIG: dict[str, Any] = {
    "dataset_path": "data/benchmarks/phase49_rna_sequences.csv",
    "strict_config_path": "configs/strict_classical_foundation.yaml",
    "benchmark_output_root": "results/phase49_benchmark",
    "calibration_output_root": "results/phase49_calibration",
    "resume": True,
    "fail_fast": False,
    "energy_tolerance": 1e-9,
}

RESULT_FIELDS = [
    "sequence_id",
    "split",
    "category",
    "source_type",
    "notes",
    "sequence",
    "sequence_length",
    "length_bucket",
    "status",
    "success",
    "error",
    "vienna_backend",
    "reference_structure",
    "reference_energy",
    "predicted_structure",
    "qubo_energy",
    "selected_solver",
    "reference_pair_count",
    "predicted_pair_count",
    "true_positives",
    "false_positives",
    "false_negatives",
    "precision",
    "recall",
    "f1_score",
    "exact_match",
    "base_pair_distance",
    "normalized_base_pair_distance",
    "candidate_pair_count",
    "candidate_stem_count",
    "qubo_variable_count",
    "quadratic_term_count",
    "exact_state_estimate",
    "total_runtime_seconds",
    "exact_solver_status",
    "greedy_solver_status",
    "simulated_annealing_status",
    "successful_solver_count",
    "solver_structure_agreement",
    "solver_energy_agreement",
    "exact_vs_greedy_structure_match",
    "exact_vs_annealing_structure_match",
    "greedy_vs_annealing_structure_match",
    "run_directory",
]


def _safe_id(raw: str | None, prefix: str) -> str:
    candidate = raw or datetime.now(timezone.utc).strftime(f"{prefix}_%Y%m%dT%H%M%SZ")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate).strip("._")
    if not cleaned:
        raise ValueError("Run identifier must contain a letter or number.")
    return cleaned


def _resolve_repo_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install requirements-phase49.txt.") from exc

    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install requirements-phase49.txt.") from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, sort_keys=False)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_benchmark_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_BENCHMARK_CONFIG)
    config_path = _resolve_repo_path(path or "configs/phase49_benchmark.yaml")
    if config_path.exists():
        config.update(_load_yaml(config_path))
    config["benchmark_config_path"] = str(config_path) if config_path.exists() else None
    return config


def load_dataset(path: str | Path) -> list[dict[str, str]]:
    dataset_path = _resolve_repo_path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Benchmark dataset was not found: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    required = {"sequence_id", "split", "category", "sequence"}
    missing = required - set(rows[0].keys() if rows else [])
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")

    seen: set[str] = set()
    normalized = []
    for line_number, row in enumerate(rows, start=2):
        sequence_id = str(row.get("sequence_id", "")).strip()
        if not sequence_id:
            raise ValueError(f"Missing sequence_id on dataset line {line_number}.")
        if sequence_id in seen:
            raise ValueError(f"Duplicate sequence_id: {sequence_id}")
        seen.add(sequence_id)

        split = str(row.get("split", "")).strip().lower()
        if split not in {"calibration", "validation"}:
            raise ValueError(
                f"Invalid split for {sequence_id}: {split}. "
                "Use calibration or validation."
            )

        sequence = clean_sequence(str(row.get("sequence", "")))
        if not validate_rna_sequence(sequence):
            raise ValueError(f"Invalid RNA sequence for {sequence_id}: {sequence}")

        normalized.append(
            {
                "sequence_id": sequence_id,
                "split": split,
                "category": str(row.get("category", "unknown")).strip() or "unknown",
                "source_type": str(row.get("source_type", "synthetic")).strip()
                or "synthetic",
                "notes": str(row.get("notes", "")).strip(),
                "sequence": sequence,
            }
        )
    return normalized


def _solver_agreement(path: Path, tolerance: float) -> dict[str, Any]:
    if not path.exists():
        return {
            "successful_solver_count": 0,
            "solver_structure_agreement": None,
            "solver_energy_agreement": None,
            "exact_solver_status": "missing",
            "greedy_solver_status": "missing",
            "simulated_annealing_status": "missing",
            "exact_vs_greedy_structure_match": None,
            "exact_vs_annealing_structure_match": None,
            "greedy_vs_annealing_structure_match": None,
        }

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    by_kind: dict[str, dict[str, str]] = {}
    successful = []
    for row in rows:
        name = str(row.get("solver", "")).lower()
        if name.startswith("exact"):
            kind = "exact"
        elif name.startswith("greedy"):
            kind = "greedy"
        elif "anneal" in name:
            kind = "annealing"
        else:
            kind = name or "unknown"
        by_kind[kind] = row
        if row.get("status") == "success" and row.get("predicted_structure"):
            successful.append(row)

    structures = {row.get("predicted_structure") for row in successful}
    energies = []
    for row in successful:
        try:
            energies.append(float(row.get("energy", "")))
        except (TypeError, ValueError):
            pass

    structure_agreement = len(structures) == 1 if len(successful) >= 2 else None
    energy_agreement = (
        max(energies) - min(energies) <= tolerance
        if len(energies) >= 2
        else None
    )

    def status(kind: str) -> str:
        return str(by_kind.get(kind, {}).get("status", "not_run"))

    def structure(kind: str) -> str | None:
        value = by_kind.get(kind, {}).get("predicted_structure")
        return value or None

    def pair_match(kind_a: str, kind_b: str) -> bool | None:
        left, right = structure(kind_a), structure(kind_b)
        return left == right if left is not None and right is not None else None

    return {
        "successful_solver_count": len(successful),
        "solver_structure_agreement": structure_agreement,
        "solver_energy_agreement": energy_agreement,
        "exact_solver_status": status("exact"),
        "greedy_solver_status": status("greedy"),
        "simulated_annealing_status": status("annealing"),
        "exact_vs_greedy_structure_match": pair_match("exact", "greedy"),
        "exact_vs_annealing_structure_match": pair_match("exact", "annealing"),
        "greedy_vs_annealing_structure_match": pair_match("greedy", "annealing"),
    }


def _result_row(
    dataset_row: dict[str, str],
    result: dict[str, Any],
    run_dir: Path,
    tolerance: float,
) -> dict[str, Any]:
    structural = result.get("structural_comparison") or {}
    runtime = result.get("runtime_summary") or {}
    vienna = result.get("vienna") or {}
    sequence = dataset_row["sequence"]
    base_pair_distance = structural.get("base_pair_distance")
    normalized_distance = (
        float(base_pair_distance) / len(sequence)
        if base_pair_distance is not None and sequence
        else None
    )

    row = {
        **dataset_row,
        "sequence_length": len(sequence),
        "length_bucket": length_bucket(len(sequence)),
        "status": "success" if result.get("strict_complete") else "partial",
        "success": bool(result.get("strict_complete")),
        "error": vienna.get("error"),
        "vienna_backend": vienna.get("backend"),
        "reference_structure": vienna.get("reference_structure"),
        "reference_energy": vienna.get("reference_energy"),
        "predicted_structure": result.get("predicted_structure"),
        "qubo_energy": result.get("qubo_energy"),
        "selected_solver": result.get("best_solver"),
        "reference_pair_count": structural.get("reference_pair_count"),
        "predicted_pair_count": structural.get("predicted_pair_count"),
        "true_positives": structural.get("true_positives"),
        "false_positives": structural.get("false_positives"),
        "false_negatives": structural.get("false_negatives"),
        "precision": structural.get("precision"),
        "recall": structural.get("recall"),
        "f1_score": structural.get("f1_score"),
        "exact_match": structural.get("exact_match"),
        "base_pair_distance": base_pair_distance,
        "normalized_base_pair_distance": (
            round(normalized_distance, 6) if normalized_distance is not None else None
        ),
        "candidate_pair_count": runtime.get("candidate_pair_count"),
        "candidate_stem_count": runtime.get("candidate_stem_count"),
        "qubo_variable_count": runtime.get("qubo_variable_count"),
        "quadratic_term_count": runtime.get("quadratic_term_count"),
        "exact_state_estimate": runtime.get("exact_state_estimate"),
        "total_runtime_seconds": runtime.get("total_runtime_seconds"),
        "run_directory": str(run_dir),
    }
    row.update(_solver_agreement(run_dir / "solver_results.csv", tolerance))
    return row


def _failed_row(dataset_row: dict[str, str], error: Exception, run_dir: Path) -> dict[str, Any]:
    sequence = dataset_row["sequence"]
    return {
        **dataset_row,
        "sequence_length": len(sequence),
        "length_bucket": length_bucket(len(sequence)),
        "status": "failed",
        "success": False,
        "error": f"{type(error).__name__}: {error}",
        "run_directory": str(run_dir),
    }


def _checkpoint_append(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _load_checkpoint(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _benchmark_report(
    run_id: str,
    split: str,
    summary: dict[str, Any],
    scaling: dict[str, Any],
    run_dir: Path,
) -> str:
    return "\n".join(
        [
            "# Phase 49 Classical Benchmark Report",
            "",
            f"- Run ID: `{run_id}`",
            f"- Split: `{split}`",
            f"- Output: `{run_dir}`",
            f"- Sequences: {summary.get('sequence_count')}",
            f"- Successful: {summary.get('successful_sequence_count')}",
            f"- Micro F1: {summary.get('micro_f1')}",
            f"- Macro F1, all cases: {summary.get('macro_f1_all')}",
            (
                "- Macro F1, non-empty ViennaRNA references: "
                f"{summary.get('macro_f1_nontrivial_reference')}"
            ),
            f"- Exact-match rate: {summary.get('exact_match_rate')}",
            (
                "- Mean normalized base-pair distance: "
                f"{summary.get('mean_normalized_base_pair_distance')}"
            ),
            (
                "- Solver structure-agreement rate: "
                f"{summary.get('solver_structure_agreement_rate')}"
            ),
            "",
            "## Interpretation boundary",
            "",
            "This is a synthetic classical benchmark against ViennaRNA MFE references. "
            "It measures agreement, disagreement, solver behavior, and computational "
            "scaling for the current QUBO formulation. It is not experimental biological "
            "validation and does not establish quantum advantage.",
            "",
            "## Scaling warning",
            "",
            str(scaling.get("warning")),
            "",
            "## Reproducibility files",
            "",
            "- `dataset_snapshot.csv`",
            "- `effective_strict_config.yaml`",
            "- `benchmark_results.csv`",
            "- `benchmark_summary.json`",
            "- `metrics_by_category.csv`",
            "- `metrics_by_length.csv`",
            "- `solver_agreement.csv`",
            "- `scaling_data.csv`",
            "- `scaling_summary.json`",
            "- `failed_runs.csv`",
            "- `checkpoint_results.jsonl`",
            "",
        ]
    )


def run_benchmark(
    *,
    dataset_path: str | Path,
    split: str,
    strict_config_path: str | Path,
    benchmark_config_path: str | Path | None = None,
    run_id: str | None = None,
    output_root: str | Path | None = None,
    limit: int | None = None,
    resume: bool | None = None,
    strict_overrides: dict[str, Any] | None = None,
    pipeline_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run the Phase 48 pipeline over a dataset split and aggregate results."""

    if split not in {"all", "calibration", "validation"}:
        raise ValueError("split must be all, calibration, or validation")

    benchmark_config = load_benchmark_config(benchmark_config_path)
    safe_run_id = _safe_id(run_id, "phase49")
    root_value = output_root or benchmark_config["benchmark_output_root"]
    root = _resolve_repo_path(root_value)
    run_dir = root / safe_run_id
    runs_dir = run_dir / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    runs_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(dataset_path)
    selected = [row for row in dataset if split == "all" or row["split"] == split]
    if limit is not None:
        selected = selected[: max(0, limit)]
    if not selected:
        raise ValueError(f"No dataset rows selected for split={split!r}.")

    strict_path = _resolve_repo_path(strict_config_path)
    strict_config = _load_yaml(strict_path)
    if strict_overrides:
        strict_config.update(strict_overrides)
    effective_config_path = run_dir / "effective_strict_config.yaml"
    _write_yaml(effective_config_path, strict_config)

    dataset_snapshot = run_dir / "dataset_snapshot.csv"
    _write_csv(
        dataset_snapshot,
        selected,
        ["sequence_id", "split", "category", "source_type", "notes", "sequence"],
    )

    manifest = {
        "phase": 49,
        "run_id": safe_run_id,
        "split": split,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(_resolve_repo_path(dataset_path)),
        "strict_config_source": str(strict_path),
        "effective_strict_config": str(effective_config_path),
        "benchmark_config": benchmark_config,
        "sequence_count": len(selected),
    }
    _write_json(run_dir / "run_manifest.json", manifest)

    use_resume = benchmark_config.get("resume", True) if resume is None else resume
    checkpoint_path = run_dir / "checkpoint_results.jsonl"
    rows = _load_checkpoint(checkpoint_path) if use_resume else []
    completed_ids = {str(row.get("sequence_id")) for row in rows}
    runner = pipeline_runner or run_pipeline
    tolerance = float(benchmark_config.get("energy_tolerance", 1e-9))

    for index, dataset_row in enumerate(selected, start=1):
        sequence_id = dataset_row["sequence_id"]
        if sequence_id in completed_ids:
            print(f"[RESUME] {sequence_id} already recorded.")
            continue

        sequence_run_dir = runs_dir / sequence_id
        print(f"[{index}/{len(selected)}] {sequence_id} ({len(dataset_row['sequence'])} nt)")
        try:
            result = runner(
                sequence=dataset_row["sequence"],
                run_id=sequence_id,
                output_folder=runs_dir,
                config_path=effective_config_path,
            )
            row = _result_row(dataset_row, result, sequence_run_dir, tolerance)
        except Exception as exc:
            row = _failed_row(dataset_row, exc, sequence_run_dir)
            print(f"[FAILED] {sequence_id}: {exc}")
            if benchmark_config.get("fail_fast", False):
                _checkpoint_append(checkpoint_path, row)
                raise

        rows.append(row)
        completed_ids.add(sequence_id)
        _checkpoint_append(checkpoint_path, row)

    selected_ids = {row["sequence_id"] for row in selected}
    rows = [row for row in rows if str(row.get("sequence_id")) in selected_ids]
    order = {row["sequence_id"]: index for index, row in enumerate(selected)}
    rows.sort(key=lambda row: order.get(str(row.get("sequence_id")), 10**9))

    summary = summarize_benchmark_rows(rows)
    scaling = summarize_scaling(rows)
    by_category = summarize_groups(rows, "category")
    by_length = summarize_groups(rows, "length_bucket")

    _write_csv(run_dir / "benchmark_results.csv", rows, RESULT_FIELDS)
    _write_json(run_dir / "benchmark_summary.json", summary)
    _write_json(run_dir / "scaling_summary.json", scaling)

    group_fields = [
        "sequence_count",
        "successful_sequence_count",
        "failed_sequence_count",
        "success_rate",
        "micro_precision",
        "micro_recall",
        "micro_f1",
        "macro_f1_all",
        "macro_f1_nontrivial_reference",
        "exact_match_rate",
        "empty_structure_accuracy",
        "mean_base_pair_distance",
        "mean_normalized_base_pair_distance",
        "solver_structure_agreement_rate",
        "mean_total_runtime_seconds",
        "mean_qubo_variable_count",
        "max_qubo_variable_count",
    ]
    _write_csv(
        run_dir / "metrics_by_category.csv",
        by_category,
        ["category", *group_fields],
    )
    _write_csv(
        run_dir / "metrics_by_length.csv",
        by_length,
        ["length_bucket", *group_fields],
    )

    solver_fields = [
        "sequence_id",
        "split",
        "category",
        "sequence_length",
        "exact_solver_status",
        "greedy_solver_status",
        "simulated_annealing_status",
        "successful_solver_count",
        "solver_structure_agreement",
        "solver_energy_agreement",
        "exact_vs_greedy_structure_match",
        "exact_vs_annealing_structure_match",
        "greedy_vs_annealing_structure_match",
    ]
    _write_csv(run_dir / "solver_agreement.csv", rows, solver_fields)

    scaling_fields = [
        "sequence_id",
        "split",
        "category",
        "sequence_length",
        "candidate_pair_count",
        "candidate_stem_count",
        "qubo_variable_count",
        "quadratic_term_count",
        "exact_state_estimate",
        "total_runtime_seconds",
    ]
    _write_csv(run_dir / "scaling_data.csv", rows, scaling_fields)

    failed = [row for row in rows if not row.get("success")]
    _write_csv(
        run_dir / "failed_runs.csv",
        failed,
        ["sequence_id", "split", "category", "sequence", "status", "error", "run_directory"],
    )

    report = _benchmark_report(safe_run_id, split, summary, scaling, run_dir)
    (run_dir / "benchmark_report.md").write_text(report, encoding="utf-8")

    return {
        "success": summary["failed_sequence_count"] == 0,
        "run_id": safe_run_id,
        "run_dir": str(run_dir),
        "rows": rows,
        "summary": summary,
        "scaling": scaling,
        "effective_strict_config": str(effective_config_path),
    }


def build_argument_parser() -> argparse.ArgumentParser:
    config = load_benchmark_config(None)
    parser = argparse.ArgumentParser(description="Run the Phase 49 RNA benchmark.")
    parser.add_argument("--dataset", default=config["dataset_path"])
    parser.add_argument("--split", choices=["all", "calibration", "validation"], default="calibration")
    parser.add_argument("--strict-config", default=config["strict_config_path"])
    parser.add_argument("--benchmark-config", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--output-root", default=config["benchmark_output_root"])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        result = run_benchmark(
            dataset_path=args.dataset,
            split=args.split,
            strict_config_path=args.strict_config,
            benchmark_config_path=args.benchmark_config,
            run_id=args.run_id,
            output_root=args.output_root,
            limit=args.limit,
            resume=not args.no_resume,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    summary = result["summary"]
    print(f"[OK] Phase 49 benchmark saved to: {result['run_dir']}")
    print(f"[OK] Successful sequences: {summary['successful_sequence_count']}/{summary['sequence_count']}")
    print(f"[OK] Micro F1: {summary['micro_f1']}")
    print(f"[OK] Exact-match rate: {summary['exact_match_rate']}")
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
