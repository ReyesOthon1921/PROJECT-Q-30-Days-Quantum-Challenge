"""
algorithm_comparison_graphs.py

Phase 20 — All Algorithm Comparison Graphs.

This module creates professional dashboard graphs comparing:
1. ViennaRNA classical benchmark
2. Greedy stem-QUBO baseline
3. Simulated annealing stem-QUBO baseline
4. QAOA readiness prototype
5. VQE readiness prototype

Important research note:
QAOA and VQE are readiness/prototype layers here. They are not presented
as final quantum advantage results.
"""

import os
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark
from src.qubo.build_qubo import build_stem_qubo
from src.evaluation.solver_comparison import compare_solvers
from src.solvers.qaoa_prototype import run_qaoa_readiness_demo
from src.solvers.vqe_prototype import run_vqe_readiness_demo


DEFAULT_OUTPUT_DIR = "static/outputs"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def find_solver_row(rows, keyword):
    if not rows:
        return {}

    for row in rows:
        solver_name = str(row.get("solver", "")).lower()
        if keyword.lower() in solver_name:
            return row

    return {}


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(9.5, 5.6))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=20, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def save_grouped_metric_chart(title, labels, precision, recall, f1, output_path):
    x_positions = list(range(len(labels)))
    width = 0.25

    plt.figure(figsize=(10, 5.8))

    plt.bar([x - width for x in x_positions], precision, width=width, label="Precision")
    plt.bar(x_positions, recall, width=width, label="Recall")
    plt.bar([x + width for x in x_positions], f1, width=width, label="F1")

    plt.title(title)
    plt.ylabel("Score")
    plt.ylim(0, 1)
    plt.xticks(x_positions, labels, rotation=20, ha="right")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def run_algorithm_comparison_graphs(sequence: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    vienna = run_vienna_benchmark(cleaned)
    qubo = build_stem_qubo(cleaned)
    comparison = compare_solvers(cleaned)
    qaoa = run_qaoa_readiness_demo(cleaned)
    vqe = run_vqe_readiness_demo(cleaned)

    comparison_rows = comparison.get("comparison_rows", [])
    greedy_row = find_solver_row(comparison_rows, "greedy")
    annealing_row = find_solver_row(comparison_rows, "annealing")

    greedy_f1 = safe_float(greedy_row.get("f1_score"))
    greedy_precision = safe_float(greedy_row.get("precision"))
    greedy_recall = safe_float(greedy_row.get("recall"))

    annealing_f1 = safe_float(annealing_row.get("f1_score"))
    annealing_precision = safe_float(annealing_row.get("precision"))
    annealing_recall = safe_float(annealing_row.get("recall"))

    vienna_runtime = safe_float(vienna.get("runtime_seconds"))
    greedy_runtime = safe_float(greedy_row.get("runtime_seconds"))
    annealing_runtime = safe_float(annealing_row.get("runtime_seconds"))

    algorithm_metrics_path = os.path.join(output_dir, "algorithm_solver_metrics.png")
    save_grouped_metric_chart(
        title="Solver Metrics: Greedy vs Simulated Annealing",
        labels=["Greedy stem-QUBO", "Simulated annealing"],
        precision=[greedy_precision, annealing_precision],
        recall=[greedy_recall, annealing_recall],
        f1=[greedy_f1, annealing_f1],
        output_path=algorithm_metrics_path,
    )

    qubit_footprint_path = os.path.join(output_dir, "algorithm_qubit_footprint.png")
    save_bar_chart(
        title="Algorithm / Model Qubit and Variable Footprint",
        labels=[
            "Full QUBO variables",
            "Estimated QUBO qubits",
            "QAOA subset qubits",
            "VQE subset qubits",
        ],
        values=[
            safe_float(qubo.get("num_variables")),
            safe_float(qubo.get("estimated_qubits")),
            safe_float(qaoa.get("problem", {}).get("estimated_qaoa_qubits")),
            safe_float(vqe.get("problem", {}).get("estimated_vqe_qubits")),
        ],
        ylabel="Count",
        output_path=qubit_footprint_path,
    )

    energy_path = os.path.join(output_dir, "algorithm_energy_objective.png")
    save_bar_chart(
        title="Exploratory Energy / Objective Comparison",
        labels=[
            "ViennaRNA MFE",
            "QAOA subset energy",
            "VQE subset energy",
        ],
        values=[
            safe_float(vienna.get("mfe_energy")),
            safe_float(qaoa.get("exact_subset_baseline", {}).get("best_energy")),
            safe_float(vqe.get("exact_subset_baseline", {}).get("best_energy")),
        ],
        ylabel="Energy / objective value",
        output_path=energy_path,
    )

    runtime_path = os.path.join(output_dir, "algorithm_runtime_comparison.png")
    save_bar_chart(
        title="Runtime Comparison",
        labels=[
            "ViennaRNA",
            "Greedy",
            "Simulated annealing",
        ],
        values=[
            vienna_runtime,
            greedy_runtime,
            annealing_runtime,
        ],
        ylabel="Runtime seconds",
        output_path=runtime_path,
    )

    generated_graphs = [
        {
            "key": "solver_metrics",
            "title": "Solver Metrics: Greedy vs Simulated Annealing",
            "filename": "algorithm_solver_metrics.png",
            "static_path": "/static/outputs/algorithm_solver_metrics.png",
        },
        {
            "key": "qubit_footprint",
            "title": "Algorithm / Model Qubit and Variable Footprint",
            "filename": "algorithm_qubit_footprint.png",
            "static_path": "/static/outputs/algorithm_qubit_footprint.png",
        },
        {
            "key": "energy_objective",
            "title": "Exploratory Energy / Objective Comparison",
            "filename": "algorithm_energy_objective.png",
            "static_path": "/static/outputs/algorithm_energy_objective.png",
        },
        {
            "key": "runtime_comparison",
            "title": "Runtime Comparison",
            "filename": "algorithm_runtime_comparison.png",
            "static_path": "/static/outputs/algorithm_runtime_comparison.png",
        },
    ]

    return {
        "success": True,
        "phase": "Phase 20 — All Algorithm Comparison Graphs",
        "sequence": cleaned,
        "length": len(cleaned),
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "summary": {
            "vienna_mfe_energy": vienna.get("mfe_energy"),
            "vienna_runtime_seconds": vienna.get("runtime_seconds"),
            "qubo_variables": qubo.get("num_variables"),
            "estimated_qubits": qubo.get("estimated_qubits"),
            "greedy_f1": greedy_f1,
            "greedy_precision": greedy_precision,
            "greedy_recall": greedy_recall,
            "annealing_f1": annealing_f1,
            "annealing_precision": annealing_precision,
            "annealing_recall": annealing_recall,
            "qaoa_subset_qubits": qaoa.get("problem", {}).get("estimated_qaoa_qubits"),
            "qaoa_best_energy": qaoa.get("exact_subset_baseline", {}).get("best_energy"),
            "vqe_subset_qubits": vqe.get("problem", {}).get("estimated_vqe_qubits"),
            "vqe_best_energy": vqe.get("exact_subset_baseline", {}).get("best_energy"),
        },
        "research_note": (
            "ViennaRNA is used as the classical benchmark. Greedy and simulated annealing "
            "are baseline optimization solvers. QAOA and VQE are readiness prototypes only, "
            "not claims of quantum advantage."
        ),
        "context_note": (
            "This update connects the RNA therapeutic motivation with QUBO/quantum optimization "
            "limitations. The dashboard now compares algorithms visually and keeps raw JSON only "
            "as a technical/debugging view."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_algorithm_comparison_graphs(sequence)

    print("Algorithm comparison graph summary")
    print("----------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"generated_graph_count: {result['generated_graph_count']}")

    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")