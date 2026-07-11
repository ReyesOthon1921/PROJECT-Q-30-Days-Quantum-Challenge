"""
qaoa_circuit.py

Phase 25 — QAOA Circuit Prototype.

This module creates a small QAOA-style circuit from the QAOA-ready QUBO subset.

Important:
This is a local simulator prototype.
It does not claim quantum advantage.
"""

import math
import time

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from src.solvers.qaoa_prototype import run_qaoa_readiness_demo


def build_qaoa_circuit_from_subset(sequence: str, gamma: float = 0.7, beta: float = 0.35) -> dict:
    """
    Build a simple one-layer QAOA-style circuit from the QAOA-ready QUBO subset.

    The circuit uses:
    - Hadamards for equal superposition
    - RZ gates for linear QUBO terms
    - CX-RZ-CX blocks for quadratic QUBO terms
    - RX gates for the mixer layer
    """
    readiness = run_qaoa_readiness_demo(sequence)
    problem = readiness["problem"]

    variables = problem["selected_variables"]
    linear_terms = problem["linear_terms"]
    quadratic_terms = problem["quadratic_terms"]

    num_qubits = len(variables)
    variable_to_qubit = {
        variable: index
        for index, variable in enumerate(variables)
    }

    circuit = QuantumCircuit(num_qubits, num_qubits)

    # Initial superposition
    for qubit in range(num_qubits):
        circuit.h(qubit)

    circuit.barrier()

    # Cost layer: linear terms
    for variable, coefficient in linear_terms.items():
        qubit = variable_to_qubit[variable]
        circuit.rz(2 * gamma * coefficient, qubit)

    # Cost layer: quadratic terms
    for term in quadratic_terms:
        var_a = term["var_a"]
        var_b = term["var_b"]
        coefficient = term["coefficient"]

        if var_a not in variable_to_qubit or var_b not in variable_to_qubit:
            continue

        q_a = variable_to_qubit[var_a]
        q_b = variable_to_qubit[var_b]

        circuit.cx(q_a, q_b)
        circuit.rz(2 * gamma * coefficient, q_b)
        circuit.cx(q_a, q_b)

    circuit.barrier()

    # Mixer layer
    for qubit in range(num_qubits):
        circuit.rx(2 * beta, qubit)

    circuit.barrier()

    # Measurement
    for qubit in range(num_qubits):
        circuit.measure(qubit, qubit)

    return {
        "success": True,
        "phase": "Phase 25 — QAOA Circuit Prototype",
        "sequence": problem["sequence"],
        "num_qubits": num_qubits,
        "variables": variables,
        "linear_term_count": len(linear_terms),
        "quadratic_term_count": len(quadratic_terms),
        "gamma": gamma,
        "beta": beta,
        "circuit": circuit,
        "readiness": readiness,
    }


def run_qaoa_circuit_simulation(sequence: str, shots: int = 512) -> dict:
    """
    Run the QAOA-style circuit on AerSimulator.
    """
    start = time.perf_counter()

    circuit_result = build_qaoa_circuit_from_subset(sequence)
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

    runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 25 — QAOA Circuit Prototype",
        "simulator": "Qiskit AerSimulator",
        "shots": shots,
        "num_qubits": circuit_result["num_qubits"],
        "linear_term_count": circuit_result["linear_term_count"],
        "quadratic_term_count": circuit_result["quadratic_term_count"],
        "gamma": circuit_result["gamma"],
        "beta": circuit_result["beta"],
        "circuit_depth": circuit.depth(),
        "transpiled_depth": transpiled_circuit.depth(),
        "circuit_size": circuit.size(),
        "top_bitstring": top_bitstring,
        "top_count": top_count,
        "top_probability": top_probability,
        "top_10_counts": sorted_counts[:10],
        "runtime_seconds": runtime_seconds,
        "note": (
            "This is a QAOA-style simulator prototype using a small QUBO subset. "
            "It is not a quantum advantage claim."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_qaoa_circuit_simulation(sequence)

    print("QAOA circuit prototype summary")
    print("------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"simulator: {result['simulator']}")
    print(f"shots: {result['shots']}")
    print(f"num_qubits: {result['num_qubits']}")
    print(f"linear_term_count: {result['linear_term_count']}")
    print(f"quadratic_term_count: {result['quadratic_term_count']}")
    print(f"circuit_depth: {result['circuit_depth']}")
    print(f"transpiled_depth: {result['transpiled_depth']}")
    print(f"top_bitstring: {result['top_bitstring']}")
    print(f"top_probability: {result['top_probability']}")
    print(f"runtime_seconds: {result['runtime_seconds']}")
    print("top_10_counts:")
    for bitstring, count in result["top_10_counts"]:
        print(f"  {bitstring}: {count}")