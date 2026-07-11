"""
qaoa_parameter_sweep.py

Phase 29 — QAOA Parameter Sweep.

This module tests multiple QAOA gamma/beta values using the small
QAOA-ready QUBO subset.

Important:
This is a local simulator parameter sweep.
It does not claim quantum advantage.
"""

import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from qiskit import transpile
from qiskit_aer import AerSimulator

from src.classical.sequence_tools import clean_sequence
from src.quantum.qaoa_circuit import build_qaoa_circuit_from_subset


DEFAULT_OUTPUT_DIR = "static/outputs"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def bitstring_to_assignment(bitstring: str, variables: list[str]) -> dict:
    """
    Convert Qiskit bitstring into variable assignment.

    Qiskit displays classical bits from highest to lowest, so we reverse
    the string to align bit index 0 with variable index 0.
    """
    reversed_bits = bitstring[::-1]

    assignment = {}
    for index, variable in enumerate(variables):
        if index < len(reversed_bits):
            assignment[variable] = int(reversed_bits[index])
        else:
            assignment[variable] = 0

    return assignment


def evaluate_qubo_energy(assignment: dict, linear_terms: dict, quadratic_terms: list[dict]) -> float:
    energy = 0.0

    for variable, coefficient in linear_terms.items():
        energy += safe_float(coefficient) * assignment.get(variable, 0)

    for term in quadratic_terms:
        var_a = term.get("var_a")
        var_b = term.get("var_b")
        coefficient = safe_float(term.get("coefficient"))

        energy += coefficient * assignment.get(var_a, 0) * assignment.get(var_b, 0)

    return round(energy, 4)


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(10, 5.8))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def run_qaoa_parameter_sweep(sequence: str, shots: int = 512, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    gamma_values = [0.2, 0.5, 0.8, 1.1]
    beta_values = [0.15, 0.35, 0.55, 0.75]

    simulator = AerSimulator()
    sweep_results = []

    best_result = None

    for gamma in gamma_values:
        for beta in beta_values:
            run_start = time.perf_counter()

            circuit_result = build_qaoa_circuit_from_subset(
                cleaned,
                gamma=gamma,
                beta=beta,
            )

            circuit = circuit_result["circuit"]
            readiness = circuit_result["readiness"]
            problem = readiness["problem"]

            variables = problem["selected_variables"]
            linear_terms = problem["linear_terms"]
            quadratic_terms = problem["quadratic_terms"]

            transpiled_circuit = transpile(circuit, simulator)
            job = simulator.run(transpiled_circuit, shots=shots)
            result = job.result()
            counts = result.get_counts()

            sorted_counts = sorted(
                counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )

            top_bitstring = sorted_counts[0][0] if sorted_counts else None
            top_count = sorted_counts[0][1] if sorted_counts else 0
            top_probability = round(top_count / shots, 4) if shots else 0.0

            assignment = bitstring_to_assignment(top_bitstring, variables) if top_bitstring else {}
            top_energy = evaluate_qubo_energy(
                assignment=assignment,
                linear_terms=linear_terms,
                quadratic_terms=quadratic_terms,
            )

            runtime_seconds = round(time.perf_counter() - run_start, 4)

            item = {
                "gamma": gamma,
                "beta": beta,
                "shots": shots,
                "num_qubits": circuit_result["num_qubits"],
                "linear_term_count": circuit_result["linear_term_count"],
                "quadratic_term_count": circuit_result["quadratic_term_count"],
                "circuit_depth": circuit.depth(),
                "transpiled_depth": transpiled_circuit.depth(),
                "circuit_size": circuit.size(),
                "top_bitstring": top_bitstring,
                "top_count": top_count,
                "top_probability": top_probability,
                "top_energy": top_energy,
                "runtime_seconds": runtime_seconds,
            }

            sweep_results.append(item)

            if best_result is None:
                best_result = item
            elif item["top_energy"] < best_result["top_energy"]:
                best_result = item

    labels = [
        f"g={item['gamma']}, b={item['beta']}"
        for item in sweep_results
    ]

    probability_graph_path = os.path.join(output_dir, "qaoa_parameter_sweep_probability.png")
    save_bar_chart(
        title="QAOA Parameter Sweep: Top Measurement Probability",
        labels=labels,
        values=[item["top_probability"] for item in sweep_results],
        ylabel="Top probability",
        output_path=probability_graph_path,
    )

    energy_graph_path = os.path.join(output_dir, "qaoa_parameter_sweep_energy.png")
    save_bar_chart(
        title="QAOA Parameter Sweep: Estimated QUBO Energy",
        labels=labels,
        values=[item["top_energy"] for item in sweep_results],
        ylabel="Estimated QUBO energy",
        output_path=energy_graph_path,
    )

    runtime_graph_path = os.path.join(output_dir, "qaoa_parameter_sweep_runtime.png")
    save_bar_chart(
        title="QAOA Parameter Sweep: Runtime",
        labels=labels,
        values=[item["runtime_seconds"] for item in sweep_results],
        ylabel="Seconds",
        output_path=runtime_graph_path,
    )

    generated_graphs = [
        {
            "key": "qaoa_sweep_probability",
            "title": "QAOA Parameter Sweep: Top Measurement Probability",
            "filename": "qaoa_parameter_sweep_probability.png",
            "static_path": "/static/outputs/qaoa_parameter_sweep_probability.png",
        },
        {
            "key": "qaoa_sweep_energy",
            "title": "QAOA Parameter Sweep: Estimated QUBO Energy",
            "filename": "qaoa_parameter_sweep_energy.png",
            "static_path": "/static/outputs/qaoa_parameter_sweep_energy.png",
        },
        {
            "key": "qaoa_sweep_runtime",
            "title": "QAOA Parameter Sweep: Runtime",
            "filename": "qaoa_parameter_sweep_runtime.png",
            "static_path": "/static/outputs/qaoa_parameter_sweep_runtime.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 29 — QAOA Parameter Sweep",
        "sequence": cleaned,
        "shots": shots,
        "parameter_count": len(sweep_results),
        "best_result": best_result,
        "sweep_results": sweep_results,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This phase tests multiple QAOA gamma/beta values on a small QUBO subset. "
            "The best setting is selected by the lowest estimated QUBO energy from the top measured bitstring. "
            "This is still a simulator prototype and does not claim quantum advantage."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_qaoa_parameter_sweep(sequence)

    print("QAOA parameter sweep summary")
    print("----------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"parameter_count: {result['parameter_count']}")
    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")

    print("best result:")
    for key, value in result["best_result"].items():
        print(f"{key}: {value}")

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")