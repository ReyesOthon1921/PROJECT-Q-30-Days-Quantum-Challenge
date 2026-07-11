"""
quantum_benchmark.py

Phase 23 — Quantum Benchmark Layer.

This module benchmarks the quantum-readiness side of the RNA/QUBO project.

It compares:
1. Full stem-QUBO problem size
2. QAOA-ready small QUBO subset
3. VQE-ready Hamiltonian subset
4. Exact subset baselines
5. Estimated qubits
6. Estimated circuit depth
7. Hamiltonian Z / ZZ terms
8. Best subset energies
9. Approximation-style ratio
10. Runtime

Important:
This is not a quantum advantage claim.
This is a quantum-readiness benchmark for the current RNA/QUBO formulation.
"""

import os
import time
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo
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


def estimate_qaoa_depth(num_qubits: int, quadratic_terms: int, p_layers: int = 1) -> int:
    """
    Simple QAOA circuit-depth estimate.

    This is not a transpiled hardware depth.
    It is a transparent planning estimate based on:
    - mixer rotations
    - cost terms
    - QAOA layer count
    """
    return int(p_layers * ((2 * num_qubits) + (2 * quadratic_terms) + 4))


def estimate_vqe_depth(num_qubits: int, z_terms: int, zz_terms: int, ansatz_layers: int = 2) -> int:
    """
    Simple VQE circuit-depth estimate.

    This is not a transpiled hardware depth.
    It estimates ansatz + measurement complexity.
    """
    return int((ansatz_layers * 3 * num_qubits) + z_terms + (2 * zz_terms))


def approximation_ratio(reference_energy, candidate_energy):
    """
    Exploratory approximation-style ratio.

    Uses absolute values because energies may be negative.
    """
    reference = abs(safe_float(reference_energy))
    candidate = abs(safe_float(candidate_energy))

    if reference == 0:
        return 0.0

    return round(candidate / reference, 4)


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


def run_quantum_benchmark(sequence: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    qubo = build_stem_qubo(cleaned)
    qaoa = run_qaoa_readiness_demo(cleaned)
    vqe = run_vqe_readiness_demo(cleaned)

    qaoa_problem = qaoa.get("problem", {})
    qaoa_exact = qaoa.get("exact_subset_baseline", {})

    vqe_problem = vqe.get("problem", {})
    vqe_hamiltonian = vqe.get("hamiltonian", {})
    vqe_exact = vqe.get("exact_subset_baseline", {})

    full_qubo_variables = qubo.get("num_variables", 0)
    full_estimated_qubits = qubo.get("estimated_qubits", 0)
    full_linear_terms = qubo.get("num_linear_terms", 0)
    full_quadratic_terms = qubo.get("num_quadratic_terms", 0)

    qaoa_subset_qubits = qaoa_problem.get("estimated_qaoa_qubits", 0)
    qaoa_subset_variables = qaoa_problem.get("selected_variable_count", 0)
    qaoa_quadratic_terms = len(qaoa_problem.get("quadratic_terms", []))
    qaoa_best_energy = qaoa_exact.get("best_energy")

    vqe_subset_qubits = vqe_problem.get("estimated_vqe_qubits", 0)
    vqe_subset_variables = vqe_problem.get("selected_variable_count", 0)
    vqe_z_terms = vqe_hamiltonian.get("num_z_terms", 0)
    vqe_zz_terms = vqe_hamiltonian.get("num_zz_terms", 0)
    vqe_best_energy = vqe_exact.get("best_energy")

    qaoa_depth = estimate_qaoa_depth(
        num_qubits=int(qaoa_subset_qubits),
        quadratic_terms=int(qaoa_quadratic_terms),
        p_layers=1,
    )

    vqe_depth = estimate_vqe_depth(
        num_qubits=int(vqe_subset_qubits),
        z_terms=int(vqe_z_terms),
        zz_terms=int(vqe_zz_terms),
        ansatz_layers=2,
    )

    qaoa_vqe_energy_ratio = approximation_ratio(
        reference_energy=qaoa_best_energy,
        candidate_energy=vqe_best_energy,
    )

    runtime_seconds = round(time.perf_counter() - start, 4)

    qubit_graph_path = os.path.join(output_dir, "quantum_benchmark_qubits.png")
    save_bar_chart(
        title="Quantum Benchmark: Qubit Footprint",
        labels=[
            "Full QUBO",
            "QAOA subset",
            "VQE subset",
        ],
        values=[
            safe_float(full_estimated_qubits),
            safe_float(qaoa_subset_qubits),
            safe_float(vqe_subset_qubits),
        ],
        ylabel="Estimated qubits",
        output_path=qubit_graph_path,
    )

    depth_graph_path = os.path.join(output_dir, "quantum_benchmark_depth.png")
    save_bar_chart(
        title="Quantum Benchmark: Estimated Circuit Depth",
        labels=[
            "QAOA depth estimate",
            "VQE depth estimate",
        ],
        values=[
            safe_float(qaoa_depth),
            safe_float(vqe_depth),
        ],
        ylabel="Estimated circuit depth",
        output_path=depth_graph_path,
    )

    energy_graph_path = os.path.join(output_dir, "quantum_benchmark_energy.png")
    save_bar_chart(
        title="Quantum Benchmark: Exact Subset Energies",
        labels=[
            "QAOA subset",
            "VQE subset",
        ],
        values=[
            safe_float(qaoa_best_energy),
            safe_float(vqe_best_energy),
        ],
        ylabel="Best subset energy",
        output_path=energy_graph_path,
    )

    hamiltonian_graph_path = os.path.join(output_dir, "quantum_benchmark_hamiltonian_terms.png")
    save_bar_chart(
        title="Quantum Benchmark: Hamiltonian Term Counts",
        labels=[
            "VQE Z terms",
            "VQE ZZ terms",
            "QAOA quadratic terms",
        ],
        values=[
            safe_float(vqe_z_terms),
            safe_float(vqe_zz_terms),
            safe_float(qaoa_quadratic_terms),
        ],
        ylabel="Term count",
        output_path=hamiltonian_graph_path,
    )

    generated_graphs = [
        {
            "key": "quantum_qubits",
            "title": "Quantum Benchmark: Qubit Footprint",
            "filename": "quantum_benchmark_qubits.png",
            "static_path": "/static/outputs/quantum_benchmark_qubits.png",
        },
        {
            "key": "quantum_depth",
            "title": "Quantum Benchmark: Estimated Circuit Depth",
            "filename": "quantum_benchmark_depth.png",
            "static_path": "/static/outputs/quantum_benchmark_depth.png",
        },
        {
            "key": "quantum_energy",
            "title": "Quantum Benchmark: Exact Subset Energies",
            "filename": "quantum_benchmark_energy.png",
            "static_path": "/static/outputs/quantum_benchmark_energy.png",
        },
        {
            "key": "quantum_hamiltonian_terms",
            "title": "Quantum Benchmark: Hamiltonian Term Counts",
            "filename": "quantum_benchmark_hamiltonian_terms.png",
            "static_path": "/static/outputs/quantum_benchmark_hamiltonian_terms.png",
        },
    ]

    metrics = {
        "sequence_length": len(cleaned),
        "full_qubo_variables": full_qubo_variables,
        "full_estimated_qubits": full_estimated_qubits,
        "full_linear_terms": full_linear_terms,
        "full_quadratic_terms": full_quadratic_terms,
        "qaoa_subset_variables": qaoa_subset_variables,
        "qaoa_subset_qubits": qaoa_subset_qubits,
        "qaoa_quadratic_terms": qaoa_quadratic_terms,
        "qaoa_estimated_depth": qaoa_depth,
        "qaoa_best_energy": qaoa_best_energy,
        "qaoa_selected_variable_count": qaoa_exact.get("selected_variable_count"),
        "vqe_subset_variables": vqe_subset_variables,
        "vqe_subset_qubits": vqe_subset_qubits,
        "vqe_z_terms": vqe_z_terms,
        "vqe_zz_terms": vqe_zz_terms,
        "vqe_estimated_depth": vqe_depth,
        "vqe_best_energy": vqe_best_energy,
        "vqe_selected_variable_count": vqe_exact.get("selected_variable_count"),
        "qaoa_vqe_energy_ratio": qaoa_vqe_energy_ratio,
        "runtime_seconds": runtime_seconds,
    }

    return {
        "success": True,
        "phase": "Phase 23 — Quantum Benchmark Layer",
        "sequence": cleaned,
        "metrics": metrics,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "qaoa_readiness": qaoa,
        "vqe_readiness": vqe,
        "research_note": (
            "This benchmark compares QAOA-ready and VQE-ready subsets against exact subset baselines. "
            "It does not claim quantum advantage. It is a readiness benchmark for the QUBO/Ising formulation."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_quantum_benchmark(sequence)

    print("Quantum benchmark summary")
    print("-------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")

    for key, value in result["metrics"].items():
        print(f"{key}: {value}")

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")