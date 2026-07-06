"""
Day 13 - IBM Quantum Hardware Lab

Project-Q 30-Day Quantum Computing Challenge

Goal:
Create a Bell-state circuit, transpile it for a backend, run it on a local
Qiskit Aer simulator, and save the results as proof of lab completion.

This connects the Day 13 concept:
Python program -> Qiskit circuit -> transpiler -> backend -> measurement results
"""

from datetime import datetime
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


def build_bell_circuit() -> QuantumCircuit:
    """
    Build a 2-qubit Bell-state circuit.

    Expected ideal result:
        00 about 50%
        11 about 50%
    """
    qc = QuantumCircuit(2, 2)

    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    return qc


def run_lab(shots: int = 1024) -> None:
    """
    Run the Bell-state circuit on a local simulator.
    """
    qc = build_bell_circuit()

    simulator = AerSimulator()
    transpiled_circuit = transpile(qc, simulator)

    job = simulator.run(transpiled_circuit, shots=shots, seed_simulator=13)
    result = job.result()
    counts = result.get_counts()

    print("Day 13 - IBM Quantum Hardware Lab")
    print("---------------------------------")
    print("Original circuit:")
    print(qc)
    print()
    print("Transpiled circuit:")
    print(transpiled_circuit)
    print()
    print("Measurement counts:")
    print(counts)
    print()

    print("Measurement percentages:")
    for state in sorted(counts):
        percentage = (counts[state] / shots) * 100
        print(f"{state}: {percentage:.2f}%")

    output_dir = Path(__file__).resolve().parent
    output_file = output_dir / "day13_results.md"

    with output_file.open("w", encoding="utf-8") as file:
        file.write("# Day 13 - IBM Quantum Hardware Lab Results\n\n")
        file.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        file.write("## Lab Focus\n\n")
        file.write(
            "This lab demonstrates how a quantum program is written in Python, "
            "converted into a Qiskit circuit, transpiled for a backend, executed, "
            "and returned as classical measurement counts.\n\n"
        )
        file.write("## Circuit\n\n")
        file.write("The circuit creates a Bell state using:\n\n")
        file.write("- Hadamard gate on qubit 0\n")
        file.write("- CNOT gate from qubit 0 to qubit 1\n")
        file.write("- Measurement of both qubits\n\n")
        file.write("## Backend\n\n")
        file.write("Local Qiskit AerSimulator\n\n")
        file.write("## Shots\n\n")
        file.write(f"{shots}\n\n")
        file.write("## Counts\n\n")
        file.write(f"`{counts}`\n\n")
        file.write("## Percentages\n\n")

        for state in sorted(counts):
            percentage = (counts[state] / shots) * 100
            file.write(f"- `{state}`: {percentage:.2f}%\n")

        file.write("\n## Interpretation\n\n")
        file.write(
            "The expected Bell-state result is mostly `00` and `11`. "
            "On an ideal simulator, the results should be close to a 50/50 split. "
            "On real IBM Quantum hardware, small amounts of `01` and `10` may appear "
            "because of noise, decoherence, gate errors, and measurement errors.\n"
        )

    print()
    print(f"Saved results to: {output_file}")


if __name__ == "__main__":
    run_lab()