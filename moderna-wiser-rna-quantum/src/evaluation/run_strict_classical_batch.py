from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.experiment_report_writer import write_csv_rows, write_text
from src.evaluation.strict_classical_pipeline import load_config, run_pipeline


BATCH_COLUMNS = [
    "sequence_id",
    "sequence",
    "sequence_length",
    "description",
    "source",
    "expected_use",
    "vienna_success",
    "vienna_method",
    "vienna_structure",
    "vienna_energy",
    "qubo_predicted_structure",
    "qubo_energy",
    "comparison_available",
    "precision",
    "recall",
    "f1_score",
    "base_pair_distance",
    "exact_match",
    "candidate_pair_count",
    "candidate_stem_count",
    "best_solver",
    "total_runtime_seconds",
    "status",
    "error",
]


def read_dataset(dataset_path: str | Path) -> List[Dict[str, str]]:
    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = [dict(row) for row in reader]

    if not rows:
        raise ValueError("Dataset contains no RNA sequences.")

    for index, row in enumerate(rows, start=1):
        if not row.get("sequence_id"):
            row["sequence_id"] = f"seq_{index:03d}"
        if not row.get("sequence"):
            raise ValueError(f"Dataset row {index} is missing a sequence.")

    return rows


def safe_sequence_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value.strip())
    return cleaned or "sequence"


def read_json_if_exists(path_value: Any) -> Dict[str, Any]:
    if not path_value:
        return {}
    path = Path(str(path_value))
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def make_batch_row(
    dataset_row: Mapping[str, str],
    pipeline_result: Mapping[str, Any] | None,
    error: str | None = None,
) -> Dict[str, Any]:
    sequence = str(dataset_row.get("sequence", "")).strip().upper().replace("T", "U")
    base = {
        "sequence_id": dataset_row.get("sequence_id", ""),
        "sequence": sequence,
        "sequence_length": len(sequence),
        "description": dataset_row.get("description", ""),
        "source": dataset_row.get("source", ""),
        "expected_use": dataset_row.get("expected_use", ""),
    }

    if pipeline_result is None:
        return {
            **base,
            "vienna_success": False,
            "vienna_method": "unavailable",
            "vienna_structure": None,
            "vienna_energy": None,
            "qubo_predicted_structure": None,
            "qubo_energy": None,
            "comparison_available": False,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "base_pair_distance": None,
            "exact_match": None,
            "candidate_pair_count": None,
            "candidate_stem_count": None,
            "best_solver": None,
            "total_runtime_seconds": None,
            "status": "failed",
            "error": error,
        }

    saved_paths = dict(pipeline_result.get("saved_paths") or {})
    structural = read_json_if_exists(saved_paths.get("structural_comparison"))
    runtime = read_json_if_exists(saved_paths.get("runtime_summary"))

    return {
        **base,
        "vienna_success": pipeline_result.get("vienna_success"),
        "vienna_method": pipeline_result.get("vienna_method"),
        "vienna_structure": pipeline_result.get("vienna_structure"),
        "vienna_energy": pipeline_result.get("vienna_energy"),
        "qubo_predicted_structure": pipeline_result.get("predicted_dotbracket"),
        "qubo_energy": pipeline_result.get("best_qubo_energy"),
        "comparison_available": structural.get("comparison_available", pipeline_result.get("structural_comparison_available")),
        "precision": structural.get("precision"),
        "recall": structural.get("recall"),
        "f1_score": structural.get("f1_score"),
        "base_pair_distance": structural.get("base_pair_distance"),
        "exact_match": structural.get("exact_match"),
        "candidate_pair_count": pipeline_result.get("candidate_pair_count"),
        "candidate_stem_count": pipeline_result.get("candidate_stem_count"),
        "best_solver": pipeline_result.get("best_solver"),
        "total_runtime_seconds": runtime.get("total_runtime_seconds"),
        "status": "completed" if pipeline_result.get("success") else "failed",
        "error": error or "",
    }


def average(values: Iterable[Any]) -> float | None:
    numbers: List[float] = []
    for value in values:
        if value in (None, "", "None"):
            continue
        numbers.append(float(value))
    if not numbers:
        return None
    return sum(numbers) / len(numbers)


def build_batch_report(batch_id: str, rows: List[Mapping[str, Any]]) -> str:
    total = len(rows)
    completed = sum(1 for row in rows if row.get("status") == "completed")
    vienna_ready = sum(1 for row in rows if str(row.get("vienna_success")) == "True" or row.get("vienna_success") is True)
    comparisons = sum(1 for row in rows if str(row.get("comparison_available")) == "True" or row.get("comparison_available") is True)
    avg_f1 = average(row.get("f1_score") for row in rows)
    avg_runtime = average(row.get("total_runtime_seconds") for row in rows)

    failed_rows = [row for row in rows if row.get("status") != "completed"]

    lines = [
        f"# Strict Classical Batch Report — {batch_id}",
        "",
        "## Summary",
        "",
        f"- Total sequences: `{total}`",
        f"- Completed pipeline runs: `{completed}`",
        f"- Vienna references available: `{vienna_ready}`",
        f"- Structural comparisons available: `{comparisons}`",
        f"- Average F1 score when available: `{avg_f1 if avg_f1 is not None else 'Not available'}`",
        f"- Average runtime seconds: `{avg_runtime if avg_runtime is not None else 'Not available'}`",
        "",
        "## Safe Claim Boundary",
        "",
        "- This batch does not claim quantum advantage.",
        "- This batch does not claim clinical accuracy.",
        "- This batch does not claim final biological validation.",
        "- ViennaRNA MFE energy and QUBO energy are diagnostic only and not physically equivalent.",
        "",
        "## Failed Sequences",
        "",
    ]

    if not failed_rows:
        lines.append("No pipeline failures were recorded.")
    else:
        for row in failed_rows:
            lines.append(f"- `{row.get('sequence_id')}`: {row.get('error')}")

    lines.extend([
        "",
        "## Output Files",
        "",
        "- `batch_summary.csv` contains the professor-ready comparison table.",
        "- Each sequence folder contains the individual strict classical report and JSON/CSV artifacts.",
        "",
    ])

    return "\n".join(lines)


def run_batch(
    dataset_path: str | Path,
    batch_id: str,
    config_path: str | None = "configs/strict_classical_foundation.yaml",
    output_root: str | Path = "results/classical_foundation_batch",
) -> Dict[str, Any]:
    config = load_config(config_path)
    dataset_rows = read_dataset(dataset_path)
    batch_dir = Path(output_root) / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: List[Dict[str, Any]] = []
    start = time.perf_counter()

    for dataset_row in dataset_rows:
        sequence_id = safe_sequence_id(str(dataset_row["sequence_id"]))
        sequence = str(dataset_row["sequence"])
        try:
            pipeline_result = run_pipeline(
                sequence=sequence,
                run_id=sequence_id,
                config=config,
                output_root=str(batch_dir),
            )
            summary_rows.append(make_batch_row(dataset_row, pipeline_result))
        except Exception as exc:
            summary_rows.append(make_batch_row(dataset_row, None, error=str(exc)))

    total_runtime = time.perf_counter() - start

    batch_summary_path = write_csv_rows(batch_dir / "batch_summary.csv", summary_rows, fieldnames=BATCH_COLUMNS)
    batch_report_path = write_text(batch_dir / "batch_report.md", build_batch_report(batch_id, summary_rows))

    return {
        "success": True,
        "batch_id": batch_id,
        "dataset_path": str(dataset_path),
        "output_dir": str(batch_dir),
        "sequence_count": len(dataset_rows),
        "completed_count": sum(1 for row in summary_rows if row.get("status") == "completed"),
        "vienna_reference_count": sum(1 for row in summary_rows if row.get("vienna_success") is True),
        "comparison_count": sum(1 for row in summary_rows if row.get("comparison_available") is True),
        "total_batch_runtime_seconds": total_runtime,
        "batch_summary": str(batch_summary_path),
        "batch_report": str(batch_report_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the strict classical RNA-QUBO pipeline for a dataset of RNA sequences.")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--batch-id", default=f"strict_classical_batch_{int(time.time())}")
    parser.add_argument("--config", default="configs/strict_classical_foundation.yaml")
    parser.add_argument("--output-root", default="results/classical_foundation_batch")
    args = parser.parse_args()

    result = run_batch(
        dataset_path=args.dataset,
        batch_id=args.batch_id,
        config_path=args.config,
        output_root=args.output_root,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
