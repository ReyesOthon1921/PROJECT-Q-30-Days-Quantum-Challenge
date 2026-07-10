"""
plot_graphs.py

Phase 19A — Paper-informed graph generation for the RNA/QUBO dashboard.

This module reads results/scaling_results.csv and creates dashboard-ready plots.

Research context:
The paper "Exploring the Boundaries of Modern Quantum Annealers with RNA
Structure Prediction" warns that QUBO-based RNA folding can fail as sequence
length scales because of:
- deep local minima
- QUBO two-body interaction limits
- overprediction of stems/base pairs
- missing higher-order RNA structural constraints

These plots help show the scaling limits of the current prototype.
"""

import csv
import os
from typing import List, Dict, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


DEFAULT_CSV_PATH = "results/scaling_results.csv"
DEFAULT_OUTPUT_DIR = "static/outputs"


def read_scaling_rows(csv_path: str = DEFAULT_CSV_PATH) -> List[Dict[str, str]]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Scaling CSV not found: {csv_path}")

    with open(csv_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader)


def find_column(rows: List[Dict[str, str]], candidates: List[str]) -> Optional[str]:
    if not rows:
        return None

    available_columns = set(rows[0].keys())

    for candidate in candidates:
        if candidate in available_columns:
            return candidate

    return None


def to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def prepare_xy(rows: List[Dict[str, str]], x_col: str, y_col: str):
    points = []

    for row in rows:
        x_value = to_float(row.get(x_col))
        y_value = to_float(row.get(y_col))

        if x_value is not None and y_value is not None:
            points.append((x_value, y_value))

    points.sort(key=lambda item: item[0])

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    return x_values, y_values


def plot_line_graph(
    rows: List[Dict[str, str]],
    x_col: str,
    y_col: str,
    title: str,
    y_label: str,
    output_path: str,
) -> bool:
    x_values, y_values = prepare_xy(rows, x_col, y_col)

    if not x_values or not y_values:
        return False

    plt.figure(figsize=(9, 5.4))
    plt.plot(x_values, y_values, marker="o", linewidth=2)
    plt.title(title)
    plt.xlabel("RNA sequence length")
    plt.ylabel(y_label)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()

    return True


def run_plot_generation(
    csv_path: str = DEFAULT_CSV_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> dict:
    rows = read_scaling_rows(csv_path)
    os.makedirs(output_dir, exist_ok=True)

    length_col = find_column(rows, ["length", "sequence_length", "rna_length"])

    if length_col is None:
        return {
            "success": False,
            "error": "No sequence length column found in scaling CSV.",
            "available_columns": list(rows[0].keys()) if rows else [],
        }

    plot_specs = [
        {
            "key": "candidate_pairs",
            "title": "Sequence Length vs Candidate Base Pairs",
            "y_label": "Candidate base pairs",
            "columns": ["candidate_pair_count", "candidate_pairs", "num_candidate_pairs"],
            "filename": "scaling_candidate_pairs.png",
        },
        {
            "key": "candidate_stems",
            "title": "Sequence Length vs Candidate Stems",
            "y_label": "Candidate stems",
            "columns": ["candidate_stem_count", "candidate_stems", "num_candidate_stems"],
            "filename": "scaling_candidate_stems.png",
        },
        {
            "key": "qubo_variables",
            "title": "Sequence Length vs QUBO Variables",
            "y_label": "QUBO variables / estimated qubits",
            "columns": ["qubo_variables", "estimated_qubits", "num_variables", "candidate_stem_count"],
            "filename": "scaling_qubo_variables.png",
        },
        {
            "key": "quadratic_terms",
            "title": "Sequence Length vs Quadratic Penalty Terms",
            "y_label": "Quadratic penalty terms",
            "columns": ["qubo_quadratic_terms", "num_quadratic_terms", "quadratic_terms"],
            "filename": "scaling_quadratic_terms.png",
        },
        {
            "key": "f1_score",
            "title": "Sequence Length vs Solver F1 Score",
            "y_label": "F1 score",
            "columns": ["f1_score", "greedy_f1_score", "greedy_f1", "f1"],
            "filename": "scaling_f1_score.png",
        },
    ]

    generated_graphs = []
    skipped_graphs = []

    for spec in plot_specs:
        y_col = find_column(rows, spec["columns"])

        if y_col is None:
            skipped_graphs.append({
                "key": spec["key"],
                "reason": "No matching CSV column found.",
                "searched_columns": spec["columns"],
            })
            continue

        output_path = os.path.join(output_dir, spec["filename"])
        was_created = plot_line_graph(
            rows=rows,
            x_col=length_col,
            y_col=y_col,
            title=spec["title"],
            y_label=spec["y_label"],
            output_path=output_path,
        )

        if was_created:
            generated_graphs.append({
                "key": spec["key"],
                "title": spec["title"],
                "csv_column": y_col,
                "filename": spec["filename"],
                "static_path": f"/static/outputs/{spec['filename']}",
            })
        else:
            skipped_graphs.append({
                "key": spec["key"],
                "reason": "No numeric data available for plot.",
                "csv_column": y_col,
            })

    return {
        "success": True,
        "phase": "Phase 19A — Paper-informed plot graph dashboard",
        "csv_path": csv_path,
        "output_dir": output_dir,
        "row_count": len(rows),
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "skipped_graphs": skipped_graphs,
        "paper_informed_note": (
            "This graph layer was added after reviewing the quantum annealer/RNA "
            "paper, which warns that QUBO RNA folding can degrade with sequence "
            "length because of local minima, two-body limits, overprediction of "
            "stems/base pairs, and missing higher-order structural constraints."
        ),
    }


if __name__ == "__main__":
    result = run_plot_generation()

    print("Plot graph generation summary")
    print("-----------------------------")
    print(f"success: {result['success']}")
    print(f"row_count: {result.get('row_count')}")
    print(f"generated_graph_count: {result.get('generated_graph_count')}")

    for graph in result.get("generated_graphs", []):
        print(f"- {graph['title']}: {graph['static_path']}")

    for skipped in result.get("skipped_graphs", []):
        print(f"skipped: {skipped}")