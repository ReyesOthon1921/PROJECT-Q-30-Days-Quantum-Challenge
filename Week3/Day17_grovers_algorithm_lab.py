"""PROJECT-Q Day 17 Lab — Grover's Algorithm.

This program searches a four-state space and amplifies
the target quantum state |11>.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.circuit.library import grover_operator
from qiskit.primitives import StatevectorSampler
from qiskit.visualization import plot_histogram


SHOTS = 1024
TARGET_STATE = "11"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIGURE_DIRECTORY = PROJECT_ROOT / "results" / "figures"
REPORT_DIRECTORY = PROJECT_ROOT / "results" / "reports"

FIGURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)


def create_oracle() -> QuantumCircuit:
    """Create an oracle that marks the target state |11>."""

    oracle = QuantumCircuit(2, name="Oracle")

    # Controlled-Z changes the phase only when both qubits are 1.
    oracle.cz(0, 1)

    return oracle


def create_grover_circuit() -> QuantumCircuit:
    """Create the complete two-qubit Grover search circuit."""

    oracle = create_oracle()

    # Construct one Grover iteration:
    # oracle phase marking followed by diffusion.
    grover_iteration = grover_operator(
        oracle,
        insert_barriers=True,
        name="Grover",
    )

    circuit = QuantumCircuit(2)

    # Place |00>, |01>, |10>, and |11> into equal superposition.
    circuit.h([0, 1])
    circuit.barrier()

    # Apply one Grover iteration.
    # One iteration is optimal for four states with one marked state.
    circuit.compose(grover_iteration, inplace=True)
    circuit.barrier()

    # Add measurements to both qubits.
    circuit.measure_all()

    return circuit


def run_lab() -> None:
    """Run, validate, display, and save the Grover experiment."""

    circuit = create_grover_circuit()

    # StatevectorSampler performs an ideal local simulation.
    sampler = StatevectorSampler(seed=42)

    job = sampler.run([circuit], shots=SHOTS)
    result = job.result()

    counts = result[0].data.meas.get_counts()
    counts = dict(sorted(counts.items()))

    winning_state = max(counts, key=counts.get)
    target_count = counts.get(TARGET_STATE, 0)
    success_rate = target_count / SHOTS

    print()
    print("PROJECT-Q DAY 17 — GROVER'S ALGORITHM")
    print("=" * 48)
    print()
    print(circuit.draw(output="text"))

    print()
    print("EXPERIMENT RESULTS")
    print("-" * 48)
    print(f"Search space:        00, 01, 10, 11")
    print(f"Expected target:     {TARGET_STATE}")
    print(f"Measurement counts: {counts}")
    print(f"Winning state:       {winning_state}")
    print(f"Target count:        {target_count}/{SHOTS}")
    print(f"Target success rate: {success_rate:.2%}")

    if winning_state != TARGET_STATE:
        raise RuntimeError(
            f"Lab failed: expected {TARGET_STATE}, "
            f"but {winning_state} was measured most frequently."
        )

    print()
    print("PASS: Grover's algorithm amplified the target state |11>.")

    histogram_path = (
        FIGURE_DIRECTORY / "day17_grover_histogram.png"
    )

    histogram = plot_histogram(
        counts,
        title="Day 17 — Grover Search for Target State |11>",
    )

    histogram.savefig(
        histogram_path,
        bbox_inches="tight",
        dpi=200,
    )
    plt.close(histogram)

    circuit_path = (
        FIGURE_DIRECTORY / "day17_grover_circuit.png"
    )

    circuit_figure = circuit.draw(
        output="mpl",
        fold=-1,
    )

    circuit_figure.savefig(
        circuit_path,
        bbox_inches="tight",
        dpi=200,
    )
    plt.close(circuit_figure)

    report_path = (
        REPORT_DIRECTORY / "day17_grover_report.txt"
    )

    report = f"""PROJECT-Q Day 17 — Grover's Algorithm Lab
================================================

Objective
---------
Search four possible two-qubit states and amplify the
marked target state |11>.

Search Space
------------
|00>
|01>
|10>
|11>

Target State
------------
|{TARGET_STATE}>

Number of Shots
---------------
{SHOTS}

Measurement Counts
------------------
{counts}

Winning State
-------------
|{winning_state}>

Target Count
------------
{target_count}/{SHOTS}

Target Success Rate
-------------------
{success_rate:.2%}

Validation
----------
PASS: The target state |{TARGET_STATE}> was measured
more frequently than every other state.

Lab Workflow
------------
1. Initialize two qubits in the |00> state.
2. Apply Hadamard gates to create equal superposition.
3. Use a Controlled-Z oracle to mark |11>.
4. Apply the Grover diffusion operation.
5. Measure both qubits.
6. Confirm that |11> dominates the measurement results.

Circuit
-------
{circuit.draw(output="text")}
"""

    report_path.write_text(report, encoding="utf-8")

    print()
    print("SAVED LAB ARTIFACTS")
    print("-" * 48)
    print(f"Report:    {report_path}")
    print(f"Histogram: {histogram_path}")
    print(f"Circuit:   {circuit_path}")


if __name__ == "__main__":
    run_lab()