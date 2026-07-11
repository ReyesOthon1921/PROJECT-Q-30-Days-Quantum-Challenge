"""
circuit_comparison.py

Phase 27 — QAOA vs VQE Circuit Comparison.

This module compares the QAOA and VQE circuit simulator prototypes
side by side.

Important:
This is a simulator-level comparison.
It does not claim quantum advantage.
"""

import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.quantum.qaoa_circuit import run_qaoa_circuit_simulation
from src.quantum.vqe_circuit import run_vqe_circuit_simulation


DEFAULT_OUTPUT_DIR = "static/outputs"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(9.5, 5.6))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def run_circuit_comparison(sequence: str, shots: int = 512, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    qaoa = run_qaoa_circuit_simulation(cleaned, shots=shots)
    vqe = run_vqe_circuit_simulation(cleaned, shots=shots)

    metrics = {
        "sequence_length": len(cleaned),
        "shots": shots,
        "qaoa_qubits": qaoa.get("num_qubits"),
        "vqe_qubits": vqe.get("num_qubits"),
        "qaoa_circuit_depth": qaoa.get("circuit_depth"),
        "vqe_circuit_depth": vqe.get("circuit_depth"),
        "qaoa_transpiled_depth": qaoa.get("transpiled_depth"),
        "vqe_transpiled_depth": vqe.get("transpiled_depth"),
        "qaoa_circuit_size": qaoa.get("circuit_size"),
        "vqe_circuit_size": vqe.get("circuit_size"),
        "qaoa_top_bitstring": qaoa.get("top_bitstring"),
        "vqe_top_bitstring": vqe.get("top_bitstring"),
        "qaoa_top_probability": qaoa.get("top_probability"),
        "vqe_top_probability": vqe.get("top_probability"),
        "qaoa_runtime_seconds": qaoa.get("runtime_seconds"),
        "vqe_runtime_seconds": vqe.get("runtime_seconds"),
        "qaoa_linear_terms": qaoa.get("linear_term_count"),
        "qaoa_quadratic_terms": qaoa.get("quadratic_term_count"),
        "vqe_z_terms": vqe.get("z_term_count"),
        "vqe_zz_terms": vqe.get("zz_term_count"),
        "vqe_exact_subset_baseline_energy": vqe.get("exact_subset_baseline_energy"),
    }

    depth_graph_path = os.path.join(output_dir, "circuit_comparison_depth.png")
    save_bar_chart(
        title="QAOA vs VQE: Circuit Depth",
        labels=["QAOA depth", "VQE depth", "QAOA transpiled", "VQE transpiled"],
        values=[
            safe_float(metrics["qaoa_circuit_depth"]),
            safe_float(metrics["vqe_circuit_depth"]),
            safe_float(metrics["qaoa_transpiled_depth"]),
            safe_float(metrics["vqe_transpiled_depth"]),
        ],
        ylabel="Depth",
        output_path=depth_graph_path,
    )

    probability_graph_path = os.path.join(output_dir, "circuit_comparison_probability.png")
    save_bar_chart(
        title="QAOA vs VQE: Top Measurement Probability",
        labels=["QAOA top probability", "VQE top probability"],
        values=[
            safe_float(metrics["qaoa_top_probability"]),
            safe_float(metrics["vqe_top_probability"]),
        ],
        ylabel="Probability",
        output_path=probability_graph_path,
    )

    runtime_graph_path = os.path.join(output_dir, "circuit_comparison_runtime.png")
    save_bar_chart(
        title="QAOA vs VQE: Runtime",
        labels=["QAOA runtime", "VQE runtime"],
        values=[
            safe_float(metrics["qaoa_runtime_seconds"]),
            safe_float(metrics["vqe_runtime_seconds"]),
        ],
        ylabel="Seconds",
        output_path=runtime_graph_path,
    )

    size_graph_path = os.path.join(output_dir, "circuit_comparison_size.png")
    save_bar_chart(
        title="QAOA vs VQE: Circuit Size",
        labels=["QAOA circuit size", "VQE circuit size"],
        values=[
            safe_float(metrics["qaoa_circuit_size"]),
            safe_float(metrics["vqe_circuit_size"]),
        ],
        ylabel="Circuit operations",
        output_path=size_graph_path,
    )

    generated_graphs = [
        {
            "key": "circuit_depth",
            "title": "QAOA vs VQE: Circuit Depth",
            "filename": "circuit_comparison_depth.png",
            "static_path": "/static/outputs/circuit_comparison_depth.png",
        },
        {
            "key": "circuit_probability",
            "title": "QAOA vs VQE: Top Measurement Probability",
            "filename": "circuit_comparison_probability.png",
            "static_path": "/static/outputs/circuit_comparison_probability.png",
        },
        {
            "key": "circuit_runtime",
            "title": "QAOA vs VQE: Runtime",
            "filename": "circuit_comparison_runtime.png",
            "static_path": "/static/outputs/circuit_comparison_runtime.png",
        },
        {
            "key": "circuit_size",
            "title": "QAOA vs VQE: Circuit Size",
            "filename": "circuit_comparison_size.png",
            "static_path": "/static/outputs/circuit_comparison_size.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 27 — QAOA vs VQE Circuit Comparison",
        "sequence": cleaned,
        "metrics": metrics,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "qaoa_summary": qaoa,
        "vqe_summary": vqe,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This comparison evaluates QAOA and VQE circuit prototypes on a local simulator. "
            "It compares circuit depth, transpiled depth, top measurement probability, runtime, and circuit size. "
            "It does not claim quantum advantage."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_circuit_comparison(sequence)

    print("QAOA vs VQE circuit comparison summary")
    print("--------------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")

    for key, value in result["metrics"].items():
        print(f"{key}: {value}")

    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")
    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")