"""
vqe_circuit.py

Phase 26 — VQE Circuit Prototype.

This module creates a small VQE-style ansatz circuit from the VQE-ready
QUBO/Ising subset.

Important:
This is a local simulator prototype.
It does not claim quantum advantage.
"""

import time

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from src.solvers.vqe_prototype import run_vqe_readiness_demo


def build_vqe_ansatz(sequence: str) -> dict:
    """
    Build a small VQE-style ansatz circuit from the VQE-ready subset.

    The ansatz uses:
    - RY/RZ rotation layers
    - CX entanglement chain
    - measurement on all qubits

    This is not a fully optimized VQE loop yet.
    It is the first circuit-level prototype.
    """
    readiness = run_vqe_readiness_demo(sequence)

    problem = readiness.get("problem", {})
    hamiltonian = readiness.get("hamiltonian", {})

    selected_variable_count = problem.get("selected_variable_count", 0)
    estimated_vqe_qubits = problem.get("estimated_vqe_qubits", selected_variable_count)

    num_qubits = int(estimated_vqe_qubits)

    if num_qubits <= 0:
        num_qubits = 1

    circuit = QuantumCircuit(num_qubits, num_qubits)

    # Fixed starter parameters.
    # Later, these can be optimized by a classical optimizer.
    theta_layer_1 = [0.35 + (0.07 * i) for i in range(num_qubits)]
    theta_layer_2 = [0.20 + (0.05 * i) for i in range(num_qubits)]

    # First rotation layer
    for qubit in range(num_qubits):
        circuit.ry(theta_layer_1[qubit], qubit)
        circuit.rz(theta_layer_1[qubit] / 2, qubit)

    circuit.barrier()

    # Entanglement layer
    for qubit in range(num_qubits - 1):
        circuit.cx(qubit, qubit + 1)

    circuit.barrier()

    # Second rotation layer
    for qubit in range(num_qubits):
        circuit.ry(theta_layer_2[qubit], qubit)
        circuit.rz(theta_layer_2[qubit] / 2, qubit)

    circuit.barrier()

    # Measurement
    for qubit in range(num_qubits):
        circuit.measure(qubit, qubit)

    return {
        "success": True,
        "phase": "Phase 26 — VQE Circuit Prototype",
        "sequence": problem.get("sequence", sequence),
        "num_qubits": num_qubits,
        "selected_variable_count": selected_variable_count,
        "z_term_count": hamiltonian.get("num_z_terms", 0),
        "zz_term_count": hamiltonian.get("num_zz_terms", 0),
        "theta_layer_1": theta_layer_1,
        "theta_layer_2": theta_layer_2,
        "circuit": circuit,
        "readiness": readiness,
    }


def run_vqe_circuit_simulation(sequence: str, shots: int = 512) -> dict:
    """
    Run the VQE-style circuit on Qiskit AerSimulator.
    """
    start = time.perf_counter()

    circuit_result = build_vqe_ansatz(sequence)
    circuit = circuit_result["circuit"]

    simulator = AerSimulator()
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

    readiness = circuit_result["readiness"]
    exact_baseline = readiness.get("exact_subset_baseline", {})
    baseline_energy = exact_baseline.get("best_energy")

    runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 26 — VQE Circuit Prototype",
        "simulator": "Qiskit AerSimulator",
        "shots": shots,
        "num_qubits": circuit_result["num_qubits"],
        "selected_variable_count": circuit_result["selected_variable_count"],
        "z_term_count": circuit_result["z_term_count"],
        "zz_term_count": circuit_result["zz_term_count"],
        "circuit_depth": circuit.depth(),
        "transpiled_depth": transpiled_circuit.depth(),
        "circuit_size": circuit.size(),
        "top_bitstring": top_bitstring,
        "top_count": top_count,
        "top_probability": top_probability,
        "exact_subset_baseline_energy": baseline_energy,
        "top_10_counts": sorted_counts[:10],
        "runtime_seconds": runtime_seconds,
        "note": (
            "This is a VQE-style simulator prototype using a small Ising/Hamiltonian-ready subset. "
            "It is not a quantum advantage claim and does not yet include a full classical optimizer loop."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_vqe_circuit_simulation(sequence)

    print("VQE circuit prototype summary")
    print("-----------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"simulator: {result['simulator']}")
    print(f"shots: {result['shots']}")
    print(f"num_qubits: {result['num_qubits']}")
    print(f"selected_variable_count: {result['selected_variable_count']}")
    print(f"z_term_count: {result['z_term_count']}")
    print(f"zz_term_count: {result['zz_term_count']}")
    print(f"circuit_depth: {result['circuit_depth']}")
    print(f"transpiled_depth: {result['transpiled_depth']}")
    print(f"top_bitstring: {result['top_bitstring']}")
    print(f"top_probability: {result['top_probability']}")
    print(f"exact_subset_baseline_energy: {result['exact_subset_baseline_energy']}")
    print(f"runtime_seconds: {result['runtime_seconds']}")
    print("top_10_counts:")
    for bitstring, count in result["top_10_counts"]:
        print(f"  {bitstring}: {count}")