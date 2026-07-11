"""
qubit_compression_estimator.py

Phase 34 — Qubit Compression Estimator.

This module estimates how many qubits could be needed under different
variable-compression models.

Important:
This is a research estimator, not a solved compressed quantum algorithm.

Clarification:
- Standard QRAO / QRAC compression is usually 2-to-1 or 3-to-1.
- The "64 variables -> 7 qubits" idea belongs to a different family:
  qubit-efficient / log-style encoding.
"""

import math
import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo


DEFAULT_OUTPUT_DIR = "static/outputs"


def compression_ratio(original_qubits: int, compressed_qubits: int) -> float:
    if compressed_qubits <= 0:
        return 0.0

    return round(original_qubits / compressed_qubits, 4)


def log_style_qubit_estimate(variable_count: int) -> int:
    """
    Qubit-efficient / log-style estimate.

    This is separate from standard QRAO.

    Example:
    64 classical variables -> ceil(log2(64)) + 1 = 7 qubits
    80 classical variables -> ceil(log2(80)) + 1 = 8 qubits
    """
    if variable_count <= 1:
        return 1

    return math.ceil(math.log2(variable_count)) + 1


def classify_risk(model_name: str) -> str:
    if model_name == "Direct one-variable-per-qubit":
        return "lowest mapping risk / highest qubit cost"

    if model_name == "2-to-1 QRAC estimate":
        return "moderate compression / moderate rounding risk"

    if model_name == "3-to-1 QRAC estimate":
        return "high compression / higher rounding risk"

    if model_name == "3-to-2 QRAC estimate":
        return "balanced compression / lower risk than 3-to-1"

    if model_name == "qubit-efficient log encoding estimate":
        return "aggressive qubit-efficient encoding estimate / separate from standard QRAO"

    return "research estimate"


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(10, 5.8))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def run_qubit_compression_estimator(sequence: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    qubo = build_stem_qubo(cleaned)

    variable_count = int(qubo.get("num_variables", 0))
    direct_qubits = max(variable_count, 1)

    two_to_one_qubits = math.ceil(variable_count / 2) if variable_count else 1
    three_to_one_qubits = math.ceil(variable_count / 3) if variable_count else 1
    three_to_two_qubits = math.ceil(variable_count / 3) * 2 if variable_count else 1
    log_encoding_qubits = log_style_qubit_estimate(variable_count)

    estimates = [
        {
            "model": "Direct one-variable-per-qubit",
            "family": "direct QUBO-to-qubit mapping",
            "variables_per_group": 1,
            "qubits_per_group": 1,
            "estimated_qubits": direct_qubits,
            "interpretation": "Current project baseline: each RNA candidate stem variable maps to one qubit.",
        },
        {
            "model": "2-to-1 QRAC estimate",
            "family": "QRAO / QRAC",
            "variables_per_group": 2,
            "qubits_per_group": 1,
            "estimated_qubits": two_to_one_qubits,
            "interpretation": "Two binary variables are estimated per compressed qubit with probabilistic rounding.",
        },
        {
            "model": "3-to-1 QRAC estimate",
            "family": "QRAO / QRAC",
            "variables_per_group": 3,
            "qubits_per_group": 1,
            "estimated_qubits": three_to_one_qubits,
            "interpretation": "Three binary variables are estimated per compressed qubit using X/Y/Z-style Pauli-axis mapping.",
        },
        {
            "model": "3-to-2 QRAC estimate",
            "family": "QRAO / QRAC",
            "variables_per_group": 3,
            "qubits_per_group": 2,
            "estimated_qubits": three_to_two_qubits,
            "interpretation": "Three binary variables are estimated using two qubits, trading less compression for lower rounding risk.",
        },
        {
            "model": "qubit-efficient log encoding estimate",
            "family": "qubit-efficient / log-style encoding",
            "variables_per_group": "all",
            "qubits_per_group": "ceil(log2(n)) + 1",
            "estimated_qubits": log_encoding_qubits,
            "interpretation": (
                "Aggressive qubit-efficient estimate. This is separate from standard QRAO. "
                "Example: 64 variables -> 7 qubits, 80 variables -> 8 qubits."
            ),
        },
    ]

    for estimate in estimates:
        estimate["compression_ratio_vs_direct"] = compression_ratio(
            original_qubits=direct_qubits,
            compressed_qubits=int(estimate["estimated_qubits"]),
        )
        estimate["risk_note"] = classify_risk(estimate["model"])

    qubit_graph_path = os.path.join(output_dir, "qubit_compression_estimator_qubits.png")
    save_bar_chart(
        title="Qubit Compression Estimator: Qubit Count",
        labels=[item["model"] for item in estimates],
        values=[item["estimated_qubits"] for item in estimates],
        ylabel="Estimated qubits",
        output_path=qubit_graph_path,
    )

    ratio_graph_path = os.path.join(output_dir, "qubit_compression_estimator_ratio.png")
    save_bar_chart(
        title="Qubit Compression Estimator: Compression Ratio",
        labels=[item["model"] for item in estimates],
        values=[item["compression_ratio_vs_direct"] for item in estimates],
        ylabel="Compression ratio vs direct",
        output_path=ratio_graph_path,
    )

    generated_graphs = [
        {
            "key": "compression_qubits",
            "title": "Qubit Compression Estimator: Qubit Count",
            "filename": "qubit_compression_estimator_qubits.png",
            "static_path": "/static/outputs/qubit_compression_estimator_qubits.png",
        },
        {
            "key": "compression_ratio",
            "title": "Qubit Compression Estimator: Compression Ratio",
            "filename": "qubit_compression_estimator_ratio.png",
            "static_path": "/static/outputs/qubit_compression_estimator_ratio.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 34 — Qubit Compression Estimator",
        "sequence": cleaned,
        "variable_count": variable_count,
        "direct_qubits": direct_qubits,
        "example_64_variables_log_encoding_qubits": log_style_qubit_estimate(64),
        "example_80_variables_log_encoding_qubits": log_style_qubit_estimate(80),
        "estimates": estimates,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This is a qubit-compression estimator. It compares direct one-variable-per-qubit mapping "
            "against QRAC/QRAO-style estimates and a separate qubit-efficient log encoding estimate. "
            "It does not solve the compressed optimization problem."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_qubit_compression_estimator(sequence)

    print("Qubit compression estimator summary")
    print("-----------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"variable_count: {result['variable_count']}")
    print(f"direct_qubits: {result['direct_qubits']}")
    print(f"64-variable log encoding example: {result['example_64_variables_log_encoding_qubits']} qubits")
    print(f"80-variable log encoding example: {result['example_80_variables_log_encoding_qubits']} qubits")
    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")

    print("estimates:")
    for item in result["estimates"]:
        print(
            f"- {item['model']}: "
            f"family={item['family']}, "
            f"estimated_qubits={item['estimated_qubits']}, "
            f"ratio={item['compression_ratio_vs_direct']}, "
            f"risk={item['risk_note']}"
        )

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")