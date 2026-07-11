"""
hardware_readiness.py

Phase 32 — Hardware Readiness Check.

This module estimates whether the current QAOA and VQE simulator circuits
are small enough for possible future quantum hardware testing.

Important:
This does not run on real IBM Quantum hardware.
It only estimates readiness from qubit count, circuit depth, gate count,
and CX count.
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
from src.quantum.vqe_circuit import build_vqe_ansatz


DEFAULT_OUTPUT_DIR = "static/outputs"


def classify_readiness(num_qubits: int, depth: int, cx_count: int) -> str:
    if num_qubits <= 10 and depth <= 80 and cx_count <= 80:
        return "small-simulator-ready / cautious hardware candidate"

    if num_qubits <= 20 and depth <= 160 and cx_count <= 160:
        return "simulator-ready / hardware challenging"

    return "not hardware-ready yet"


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(9.5, 5.6))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def summarize_circuit(name: str, circuit, simulator) -> dict:
    transpiled = transpile(circuit, simulator)
    ops = transpiled.count_ops()

    cx_count = int(ops.get("cx", 0))
    depth = int(transpiled.depth())
    size = int(transpiled.size())
    num_qubits = int(circuit.num_qubits)

    return {
        "name": name,
        "num_qubits": num_qubits,
        "original_depth": int(circuit.depth()),
        "transpiled_depth": depth,
        "circuit_size": size,
        "cx_count": cx_count,
        "operation_counts": dict(ops),
        "readiness": classify_readiness(num_qubits, depth, cx_count),
    }


def run_hardware_readiness_check(sequence: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    simulator = AerSimulator()

    qaoa_result = build_qaoa_circuit_from_subset(cleaned)
    vqe_result = build_vqe_ansatz(cleaned)

    qaoa_summary = summarize_circuit(
        name="QAOA Circuit Prototype",
        circuit=qaoa_result["circuit"],
        simulator=simulator,
    )

    vqe_summary = summarize_circuit(
        name="VQE Circuit Prototype",
        circuit=vqe_result["circuit"],
        simulator=simulator,
    )

    summaries = [qaoa_summary, vqe_summary]

    depth_graph_path = os.path.join(output_dir, "hardware_readiness_depth.png")
    save_bar_chart(
        title="Hardware Readiness: Transpiled Depth",
        labels=[item["name"] for item in summaries],
        values=[item["transpiled_depth"] for item in summaries],
        ylabel="Transpiled depth",
        output_path=depth_graph_path,
    )

    cx_graph_path = os.path.join(output_dir, "hardware_readiness_cx.png")
    save_bar_chart(
        title="Hardware Readiness: CX Gate Count",
        labels=[item["name"] for item in summaries],
        values=[item["cx_count"] for item in summaries],
        ylabel="CX gates",
        output_path=cx_graph_path,
    )

    qubit_graph_path = os.path.join(output_dir, "hardware_readiness_qubits.png")
    save_bar_chart(
        title="Hardware Readiness: Qubit Count",
        labels=[item["name"] for item in summaries],
        values=[item["num_qubits"] for item in summaries],
        ylabel="Qubits",
        output_path=qubit_graph_path,
    )

    generated_graphs = [
        {
            "key": "hardware_depth",
            "title": "Hardware Readiness: Transpiled Depth",
            "filename": "hardware_readiness_depth.png",
            "static_path": "/static/outputs/hardware_readiness_depth.png",
        },
        {
            "key": "hardware_cx",
            "title": "Hardware Readiness: CX Gate Count",
            "filename": "hardware_readiness_cx.png",
            "static_path": "/static/outputs/hardware_readiness_cx.png",
        },
        {
            "key": "hardware_qubits",
            "title": "Hardware Readiness: Qubit Count",
            "filename": "hardware_readiness_qubits.png",
            "static_path": "/static/outputs/hardware_readiness_qubits.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 32 — Hardware Readiness Check",
        "sequence": cleaned,
        "hardware_run": False,
        "backend_used": "Local Qiskit AerSimulator transpilation only",
        "summaries": summaries,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This phase does not run on real hardware. It estimates future hardware readiness "
            "using qubit count, transpiled depth, circuit size, and CX gate count."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_hardware_readiness_check(sequence)

    print("Hardware readiness summary")
    print("--------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"backend_used: {result['backend_used']}")
    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")

    for item in result["summaries"]:
        print(f"{item['name']}:")
        print(f"  num_qubits: {item['num_qubits']}")
        print(f"  transpiled_depth: {item['transpiled_depth']}")
        print(f"  circuit_size: {item['circuit_size']}")
        print(f"  cx_count: {item['cx_count']}")
        print(f"  readiness: {item['readiness']}")

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")