"""
Quantum circuit module for Mini Project 2:
Quantum Communication Dashboard.

This file contains three Qiskit simulations:

1. Bell State
2. Quantum Entanglement
3. Quantum Teleportation

Each function returns:
- title
- description
- circuit text
- measurement counts
- histogram image path
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram


OUTPUT_DIR = Path("static") / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BACKEND = AerSimulator()
SHOTS = 1000


def save_histogram(counts, filename):
    """
    Save a histogram image for measurement counts.
    """
    output_path = OUTPUT_DIR / filename

    fig = plot_histogram(counts)
    fig.savefig(output_path, bbox_inches="tight")

    return f"outputs/{filename}"


def run_bell_state():
    """
    Create and simulate a Bell State.

    Bell State idea:
    - Apply H gate to q0.
    - Apply CX/CNOT from q0 to q1.
    - Measure both qubits.

    Expected result:
    Mostly 00 and 11 outcomes.
    """
    qc = QuantumCircuit(2, 2)

    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    transpiled = transpile(qc, BACKEND)
    result = BACKEND.run(transpiled, shots=SHOTS).result()
    counts = result.get_counts()

    image_path = save_histogram(counts, "bell_state_histogram.png")

    return {
        "title": "Bell State",
        "description": (
            "A Bell State is a simple entangled two-qubit state. "
            "After the H and CNOT gates, the measurement results should be correlated."
        ),
        "circuit_text": str(qc.draw(output="text")),
        "counts": counts,
        "image_path": image_path,
        "analysis": (
            "The Bell State should mainly produce 00 and 11. "
            "This shows strong correlation between the two qubits."
        ),
    }


def run_entanglement():
    """
    Demonstrate quantum entanglement.

    This circuit is similar to the Bell State circuit because Bell States
    are one of the clearest ways to demonstrate entanglement.
    """
    qc = QuantumCircuit(2, 2)

    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    transpiled = transpile(qc, BACKEND)
    result = BACKEND.run(transpiled, shots=SHOTS).result()
    counts = result.get_counts()

    image_path = save_histogram(counts, "entanglement_histogram.png")

    count_00 = counts.get("00", 0)
    count_11 = counts.get("11", 0)
    count_01 = counts.get("01", 0)
    count_10 = counts.get("10", 0)

    correlated = count_00 + count_11
    uncorrelated = count_01 + count_10

    return {
        "title": "Quantum Entanglement",
        "description": (
            "Entanglement means the qubits are connected in a way where "
            "measuring one qubit gives information about the other."
        ),
        "circuit_text": str(qc.draw(output="text")),
        "counts": counts,
        "image_path": image_path,
        "analysis": (
            f"Correlated outcomes 00 + 11: {correlated}. "
            f"Uncorrelated outcomes 01 + 10: {uncorrelated}. "
            "The high number of correlated outcomes demonstrates entanglement."
        ),
    }


def run_teleportation():
    """
    Simulate a simple quantum teleportation-style circuit.

    We prepare q0 as |1>, create an entangled pair between q1 and q2,
    then use teleportation correction logic so the state is transferred
    to q2.

    This version avoids conditional classical operations to keep it beginner-friendly.
    """
    qc = QuantumCircuit(3, 1)

    # Prepare the input state |1> on q0.
    qc.x(0)

    # Create Bell pair between q1 and q2.
    qc.h(1)
    qc.cx(1, 2)

    # Bell measurement preparation between q0 and q1.
    qc.cx(0, 1)
    qc.h(0)

    # Coherent correction operations.
    qc.cx(1, 2)
    qc.cz(0, 2)

    # Measure the receiver qubit q2.
    qc.measure(2, 0)

    transpiled = transpile(qc, BACKEND)
    result = BACKEND.run(transpiled, shots=SHOTS).result()
    counts = result.get_counts()

    image_path = save_histogram(counts, "teleportation_histogram.png")

    return {
        "title": "Quantum Teleportation",
        "description": (
            "Quantum teleportation transfers quantum information from one qubit "
            "to another using entanglement and correction operations."
        ),
        "circuit_text": str(qc.draw(output="text")),
        "counts": counts,
        "image_path": image_path,
        "analysis": (
            "The input state was prepared as |1>. "
            "The receiver qubit should mostly measure as 1, showing the transfer."
        ),
    }