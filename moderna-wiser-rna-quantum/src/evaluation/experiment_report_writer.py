from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


def ensure_output_dir(output_dir: str | Path) -> Path:
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: str | Path, data: Mapping[str, Any] | list[Any]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return output_path


def write_text(path: str | Path, text: str) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def write_csv_rows(path: str | Path, rows: Iterable[Mapping[str, Any]], fieldnames: Optional[List[str]] = None) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    if fieldnames is None:
        fieldnames = []
        for row in row_list:
            for key in row.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in row_list:
            writer.writerow(row)
    return output_path


def _format_optional(value: Any) -> str:
    return "Not available" if value is None else str(value)


def build_experiment_report(
    run_id: str,
    sequence: str,
    vienna_reference: Mapping[str, Any],
    predicted_structure: Mapping[str, Any],
    structural_comparison: Mapping[str, Any],
    energy_comparison: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    config: Optional[Mapping[str, Any]] = None,
) -> str:
    timestamp = datetime.now().isoformat(timespec="seconds")
    lines = [
        f"# Strict Classical Foundation Experiment Report — {run_id}",
        "",
        "## Purpose",
        "",
        "This report records one reproducible classical RNA-QUBO benchmark run.",
        "",
        "## Run Metadata",
        "",
        f"- Run ID: `{run_id}`",
        f"- Timestamp: `{timestamp}`",
        f"- Input sequence: `{sequence}`",
        "",
        "## ViennaRNA Reference",
        "",
        f"- RNAfold success: `{vienna_reference.get('success')}`",
        f"- Vienna method: `{_format_optional(vienna_reference.get('vienna_method'))}`",
        f"- Reference structure: `{_format_optional(vienna_reference.get('reference_structure'))}`",
        f"- Reference energy: `{_format_optional(vienna_reference.get('reference_energy'))}`",
        f"- Runtime seconds: `{_format_optional(vienna_reference.get('runtime_seconds'))}`",
        f"- Error: `{_format_optional(vienna_reference.get('error'))}`",
        "",
        "## Predicted Structure",
        "",
        f"- Predicted dot-bracket: `{_format_optional(predicted_structure.get('predicted_dotbracket'))}`",
        f"- Predicted pairs: `{_format_optional(predicted_structure.get('predicted_pairs'))}`",
        f"- Solver used: `{_format_optional(predicted_structure.get('solver'))}`",
        f"- QUBO energy: `{_format_optional(predicted_structure.get('qubo_energy'))}`",
        "",
        "## Structural Comparison",
        "",
        f"- Comparison available: `{_format_optional(structural_comparison.get('comparison_available'))}`",
        f"- Exact match: `{_format_optional(structural_comparison.get('exact_match'))}`",
        f"- Precision: `{_format_optional(structural_comparison.get('precision'))}`",
        f"- Recall: `{_format_optional(structural_comparison.get('recall'))}`",
        f"- F1 score: `{_format_optional(structural_comparison.get('f1_score'))}`",
        f"- Base-pair distance: `{_format_optional(structural_comparison.get('base_pair_distance'))}`",
        "",
        "## Diagnostic Energy Comparison",
        "",
        f"- Comparison available: `{_format_optional(energy_comparison.get('comparison_available'))}`",
        f"- ViennaRNA reference energy: `{_format_optional(energy_comparison.get('reference_energy'))}`",
        f"- QUBO energy: `{_format_optional(energy_comparison.get('qubo_energy'))}`",
        f"- Energy difference: `{_format_optional(energy_comparison.get('energy_difference'))}`",
        f"- Absolute energy difference: `{_format_optional(energy_comparison.get('absolute_energy_difference'))}`",
        "",
        "Important note: ViennaRNA MFE energy and QUBO energy are different scoring systems. This comparison is diagnostic only and should not be treated as physical equivalence.",
        "",
        "## Runtime Summary",
        "",
        f"- Step count: `{_format_optional(runtime_summary.get('step_count'))}`",
        f"- Total runtime seconds: `{_format_optional(runtime_summary.get('total_runtime_seconds'))}`",
        f"- Slowest step: `{_format_optional(runtime_summary.get('slowest_step'))}`",
        "",
        "## Safe Claim Boundary",
        "",
        "- This run does not claim quantum advantage.",
        "- This run does not claim clinical accuracy.",
        "- This run does not claim final biological validation.",
        "- This run supports a reproducible classical benchmark bridge before deeper QAOA/VQE work.",
        "",
    ]
    if config is not None:
        lines.extend(["## Configuration Snapshot", "", "```json", json.dumps(config, indent=2), "```", ""])
    return "\n".join(lines)


def save_experiment_outputs(
    output_dir: str | Path,
    run_id: str,
    sequence: str,
    vienna_reference: Mapping[str, Any],
    candidate_pairs: list[Mapping[str, Any]],
    candidate_stems: list[Mapping[str, Any]],
    qubo_summary: list[Mapping[str, Any]],
    solver_results: list[Mapping[str, Any]],
    predicted_structure: Mapping[str, Any],
    structural_comparison: Mapping[str, Any],
    energy_comparison: Mapping[str, Any],
    runtime_summary: Mapping[str, Any],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, str]:
    base_dir = ensure_output_dir(output_dir)
    paths: Dict[str, str] = {}
    paths["input_sequence"] = str(write_text(base_dir / "input_sequence.txt", sequence + "\n"))
    paths["vienna_reference"] = str(write_json(base_dir / "vienna_reference.json", vienna_reference))
    paths["candidate_pairs"] = str(write_csv_rows(base_dir / "candidate_pairs.csv", candidate_pairs))
    paths["candidate_stems"] = str(write_csv_rows(base_dir / "candidate_stems.csv", candidate_stems))
    paths["qubo_summary"] = str(write_csv_rows(base_dir / "qubo_summary.csv", qubo_summary))
    paths["solver_results"] = str(write_csv_rows(base_dir / "solver_results.csv", solver_results))
    paths["predicted_structure"] = str(write_json(base_dir / "predicted_structure.json", predicted_structure))
    paths["structural_comparison"] = str(write_json(base_dir / "structural_comparison.json", structural_comparison))
    paths["energy_comparison"] = str(write_json(base_dir / "energy_comparison.json", energy_comparison))
    paths["runtime_summary"] = str(write_json(base_dir / "runtime_summary.json", runtime_summary))
    if config is not None:
        paths["config_snapshot"] = str(write_json(base_dir / "config_snapshot.json", config))
    report_text = build_experiment_report(
        run_id=run_id,
        sequence=sequence,
        vienna_reference=vienna_reference,
        predicted_structure=predicted_structure,
        structural_comparison=structural_comparison,
        energy_comparison=energy_comparison,
        runtime_summary=runtime_summary,
        config=config,
    )
    paths["experiment_report"] = str(write_text(base_dir / "experiment_report.md", report_text))
    manifest_rows = [{"artifact": artifact, "path": path} for artifact, path in sorted(paths.items())]
    paths["artifact_manifest"] = str(write_csv_rows(base_dir / "artifact_manifest.csv", manifest_rows, ["artifact", "path"]))
    return paths
