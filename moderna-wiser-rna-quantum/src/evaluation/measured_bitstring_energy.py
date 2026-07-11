"""
measured_bitstring_energy.py

Phase 31 — Measured Bitstring Energy Evaluation.

This module converts measured QAOA/VQE simulator bitstrings back into
QUBO assignments and estimates their QUBO energy.

Important:
This is a simulator-level energy evaluation step.
It does not claim quantum advantage.
"""

import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.evaluation.qaoa_parameter_sweep import (
    bitstring_to_assignment,
    evaluate_qubo_energy,
    run_qaoa_parameter_sweep,
)
from src.quantum.qaoa_circuit import build_qaoa_circuit_from_subset, run_qaoa_circuit_simulation
from src.quantum.vqe_circuit import run_vqe_circuit_simulation


DEFAULT_OUTPUT_DIR = "static/outputs"


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


def run_measured_bitstring_energy(sequence: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    circuit_subset = build_qaoa_circuit_from_subset(cleaned)
    problem = circuit_subset["readiness"]["problem"]

    variables = problem["selected_variables"]
    linear_terms = problem["linear_terms"]
    quadratic_terms = problem["quadratic_terms"]

    qaoa_circuit = run_qaoa_circuit_simulation(cleaned)
    vqe_circuit = run_vqe_circuit_simulation(cleaned)
    qaoa_sweep = run_qaoa_parameter_sweep(cleaned)

    candidates = [
        {
            "source": "QAOA Circuit Prototype",
            "bitstring": qaoa_circuit.get("top_bitstring"),
            "probability": qaoa_circuit.get("top_probability"),
        },
        {
            "source": "VQE Circuit Prototype",
            "bitstring": vqe_circuit.get("top_bitstring"),
            "probability": vqe_circuit.get("top_probability"),
        },
        {
            "source": "QAOA Parameter Sweep Best",
            "bitstring": qaoa_sweep.get("best_result", {}).get("top_bitstring"),
            "probability": qaoa_sweep.get("best_result", {}).get("top_probability"),
        },
    ]

    evaluated_results = []

    for candidate in candidates:
        bitstring = candidate["bitstring"]

        if bitstring:
            assignment = bitstring_to_assignment(bitstring, variables)
            energy = evaluate_qubo_energy(
                assignment=assignment,
                linear_terms=linear_terms,
                quadratic_terms=quadratic_terms,
            )
            selected_count = sum(assignment.values())
        else:
            assignment = {}
            energy = None
            selected_count = 0

        evaluated_results.append(
            {
                "source": candidate["source"],
                "bitstring": bitstring,
                "probability": candidate["probability"],
                "estimated_qubo_energy": energy,
                "selected_variable_count": selected_count,
                "assignment": assignment,
            }
        )

    valid_results = [
        item for item in evaluated_results
        if item["estimated_qubo_energy"] is not None
    ]

    best_result = min(
        valid_results,
        key=lambda item: item["estimated_qubo_energy"],
    ) if valid_results else None

    graph_path = os.path.join(output_dir, "measured_bitstring_energy.png")
    save_bar_chart(
        title="Measured Bitstring Energy Evaluation",
        labels=[item["source"] for item in valid_results],
        values=[item["estimated_qubo_energy"] for item in valid_results],
        ylabel="Estimated QUBO energy",
        output_path=graph_path,
    )

    probability_graph_path = os.path.join(output_dir, "measured_bitstring_probability.png")
    save_bar_chart(
        title="Measured Bitstring Top Probability",
        labels=[item["source"] for item in valid_results],
        values=[item["probability"] for item in valid_results],
        ylabel="Top probability",
        output_path=probability_graph_path,
    )

    generated_graphs = [
        {
            "key": "measured_bitstring_energy",
            "title": "Measured Bitstring Energy Evaluation",
            "filename": "measured_bitstring_energy.png",
            "static_path": "/static/outputs/measured_bitstring_energy.png",
        },
        {
            "key": "measured_bitstring_probability",
            "title": "Measured Bitstring Top Probability",
            "filename": "measured_bitstring_probability.png",
            "static_path": "/static/outputs/measured_bitstring_probability.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 31 — Measured Bitstring Energy Evaluation",
        "sequence": cleaned,
        "variable_count": len(variables),
        "evaluated_results": evaluated_results,
        "best_result": best_result,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This phase converts measured simulator bitstrings back into QUBO assignments "
            "and estimates their QUBO energy. It evaluates whether measured outputs correspond "
            "to better or worse QUBO objective values."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_measured_bitstring_energy(sequence)

    print("Measured bitstring energy summary")
    print("---------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"variable_count: {result['variable_count']}")
    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")

    print("best result:")
    for key, value in result["best_result"].items():
        if key != "assignment":
            print(f"{key}: {value}")

    print("all evaluated results:")
    for item in result["evaluated_results"]:
        print(f"- {item['source']}: bitstring={item['bitstring']}, energy={item['estimated_qubo_energy']}, probability={item['probability']}")

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")