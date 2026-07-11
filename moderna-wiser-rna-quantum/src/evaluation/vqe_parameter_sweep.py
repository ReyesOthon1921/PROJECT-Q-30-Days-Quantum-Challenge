"""
vqe_parameter_sweep.py

Phase 30 — VQE Parameter Sweep.

This module tests multiple simple VQE ansatz parameter settings using
a small VQE-ready Hamiltonian subset.

Important:
This is a simulator-level parameter sweep.
It is not a full VQE optimizer loop and does not claim quantum advantage.
"""

import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from src.classical.sequence_tools import clean_sequence
from src.solvers.vqe_prototype import run_vqe_readiness_demo


DEFAULT_OUTPUT_DIR = "static/outputs"


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def build_custom_vqe_circuit(num_qubits: int, angle_scale: float, entanglement_mode: str) -> QuantumCircuit:
    circuit = QuantumCircuit(num_qubits, num_qubits)

    for qubit in range(num_qubits):
        theta = angle_scale * (0.25 + 0.08 * qubit)
        circuit.ry(theta, qubit)
        circuit.rz(theta / 2, qubit)

    circuit.barrier()

    if entanglement_mode == "chain":
        for qubit in range(num_qubits - 1):
            circuit.cx(qubit, qubit + 1)

    elif entanglement_mode == "reverse_chain":
        for qubit in range(num_qubits - 1, 0, -1):
            circuit.cx(qubit, qubit - 1)

    circuit.barrier()

    for qubit in range(num_qubits):
        theta = angle_scale * (0.15 + 0.05 * qubit)
        circuit.ry(theta, qubit)
        circuit.rz(theta / 2, qubit)

    circuit.barrier()

    for qubit in range(num_qubits):
        circuit.measure(qubit, qubit)

    return circuit


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


def run_vqe_parameter_sweep(sequence: str, shots: int = 512, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    readiness = run_vqe_readiness_demo(cleaned)
    problem = readiness.get("problem", {})
    hamiltonian = readiness.get("hamiltonian", {})
    exact_baseline = readiness.get("exact_subset_baseline", {})

    num_qubits = int(problem.get("estimated_vqe_qubits", problem.get("selected_variable_count", 1)))

    if num_qubits <= 0:
        num_qubits = 1

    angle_scales = [0.5, 0.8, 1.1, 1.4]
    entanglement_modes = ["chain", "reverse_chain"]

    simulator = AerSimulator()
    sweep_results = []
    best_result = None

    for angle_scale in angle_scales:
        for entanglement_mode in entanglement_modes:
            run_start = time.perf_counter()

            circuit = build_custom_vqe_circuit(
                num_qubits=num_qubits,
                angle_scale=angle_scale,
                entanglement_mode=entanglement_mode,
            )

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
            runtime_seconds = round(time.perf_counter() - run_start, 4)

            item = {
                "angle_scale": angle_scale,
                "entanglement_mode": entanglement_mode,
                "shots": shots,
                "num_qubits": num_qubits,
                "z_term_count": hamiltonian.get("num_z_terms", 0),
                "zz_term_count": hamiltonian.get("num_zz_terms", 0),
                "circuit_depth": circuit.depth(),
                "transpiled_depth": transpiled_circuit.depth(),
                "circuit_size": circuit.size(),
                "top_bitstring": top_bitstring,
                "top_count": top_count,
                "top_probability": top_probability,
                "exact_subset_baseline_energy": exact_baseline.get("best_energy"),
                "runtime_seconds": runtime_seconds,
            }

            sweep_results.append(item)

            if best_result is None:
                best_result = item
            elif item["top_probability"] > best_result["top_probability"]:
                best_result = item

    labels = [
        f"{item['entanglement_mode']}, a={item['angle_scale']}"
        for item in sweep_results
    ]

    probability_graph_path = os.path.join(output_dir, "vqe_parameter_sweep_probability.png")
    save_bar_chart(
        title="VQE Parameter Sweep: Top Measurement Probability",
        labels=labels,
        values=[item["top_probability"] for item in sweep_results],
        ylabel="Top probability",
        output_path=probability_graph_path,
    )

    depth_graph_path = os.path.join(output_dir, "vqe_parameter_sweep_depth.png")
    save_bar_chart(
        title="VQE Parameter Sweep: Circuit Depth",
        labels=labels,
        values=[item["transpiled_depth"] for item in sweep_results],
        ylabel="Transpiled depth",
        output_path=depth_graph_path,
    )

    runtime_graph_path = os.path.join(output_dir, "vqe_parameter_sweep_runtime.png")
    save_bar_chart(
        title="VQE Parameter Sweep: Runtime",
        labels=labels,
        values=[item["runtime_seconds"] for item in sweep_results],
        ylabel="Seconds",
        output_path=runtime_graph_path,
    )

    generated_graphs = [
        {
            "key": "vqe_sweep_probability",
            "title": "VQE Parameter Sweep: Top Measurement Probability",
            "filename": "vqe_parameter_sweep_probability.png",
            "static_path": "/static/outputs/vqe_parameter_sweep_probability.png",
        },
        {
            "key": "vqe_sweep_depth",
            "title": "VQE Parameter Sweep: Circuit Depth",
            "filename": "vqe_parameter_sweep_depth.png",
            "static_path": "/static/outputs/vqe_parameter_sweep_depth.png",
        },
        {
            "key": "vqe_sweep_runtime",
            "title": "VQE Parameter Sweep: Runtime",
            "filename": "vqe_parameter_sweep_runtime.png",
            "static_path": "/static/outputs/vqe_parameter_sweep_runtime.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 30 — VQE Parameter Sweep",
        "sequence": cleaned,
        "shots": shots,
        "parameter_count": len(sweep_results),
        "best_result": best_result,
        "sweep_results": sweep_results,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This phase tests multiple simple VQE ansatz settings. "
            "It is not a full optimizer loop and does not claim quantum advantage."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_vqe_parameter_sweep(sequence)

    print("VQE parameter sweep summary")
    print("---------------------------")
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