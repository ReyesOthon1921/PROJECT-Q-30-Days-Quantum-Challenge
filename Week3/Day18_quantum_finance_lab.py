"""PROJECT-Q Day 18 - Quantum Finance Lab.

This educational lab uses four qubits to represent four investment
decisions. It samples candidate portfolios from a parameterized
quantum circuit.

This is not a complete portfolio optimizer and is not investment advice.
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.visualization import plot_histogram


SHOTS = 1024
SEED = 42

ASSET_NAMES = ("A", "B", "C", "D")
ROTATION_ANGLES = (0.8, 1.2, 0.5, 1.0)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FIGURE_DIRECTORY = PROJECT_ROOT / "results" / "figures"
REPORT_DIRECTORY = PROJECT_ROOT / "results" / "reports"
DATA_DIRECTORY = PROJECT_ROOT / "results" / "data"

FIGURE_DIRECTORY.mkdir(parents=True, exist_ok=True)
REPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


def build_quantum_finance_circuit() -> QuantumCircuit:
    """Build the four-qubit candidate portfolio circuit."""

    circuit = QuantumCircuit(4)

    # Each qubit represents one asset:
    # q0 = Asset A
    # q1 = Asset B
    # q2 = Asset C
    # q3 = Asset D

    # Prepare all 16 possible portfolios in superposition.
    circuit.h(range(4))
    circuit.barrier()

    # Adjust the probability associated with each investment decision.
    for qubit, angle in enumerate(ROTATION_ANGLES):
        circuit.ry(angle, qubit)

    circuit.barrier()

    # Create a measurement register named "meas".
    circuit.measure_all()

    return circuit


def convert_to_asset_order(
    raw_counts: dict[str, int],
) -> dict[str, int]:
    """Convert Qiskit bitstrings into Asset A-B-C-D order.

    Qiskit normally displays measured bits as q3 q2 q1 q0.

    This lab maps:
        q0 = A
        q1 = B
        q2 = C
        q3 = D

    Reversing the string makes the displayed order A B C D.
    """

    converted_counts: dict[str, int] = {}

    for raw_bits, count in raw_counts.items():
        clean_bits = raw_bits.replace(" ", "")
        asset_bits = clean_bits[::-1]

        converted_counts[asset_bits] = (
            converted_counts.get(asset_bits, 0) + count
        )

    return dict(sorted(converted_counts.items()))


def selected_assets(bits: str) -> str:
    """Return a readable description of a portfolio bitstring."""

    selected = [
        asset
        for asset, bit in zip(ASSET_NAMES, bits)
        if bit == "1"
    ]

    if not selected:
        return "No assets selected"

    return ", ".join(selected)


def save_histogram(
    counts: dict[str, int],
) -> Path:
    """Save the portfolio measurement histogram."""

    output_path = (
        FIGURE_DIRECTORY
        / "day18_portfolio_histogram.png"
    )

    figure = plot_histogram(
        counts,
        title=(
            "Day 18 - Quantum Finance Portfolio Samples "
            "(A B C D order)"
        ),
    )

    figure.savefig(
        output_path,
        bbox_inches="tight",
        dpi=200,
    )

    plt.close(figure)

    return output_path


def save_circuit_image(
    circuit: QuantumCircuit,
) -> Path:
    """Save the quantum circuit visualization."""

    output_path = (
        FIGURE_DIRECTORY
        / "day18_quantum_finance_circuit.png"
    )

    figure = circuit.draw(
        output="mpl",
        fold=-1,
    )

    figure.savefig(
        output_path,
        bbox_inches="tight",
        dpi=200,
    )

    plt.close(figure)

    return output_path


def save_csv(
    counts: dict[str, int],
) -> Path:
    """Save all measured portfolios as CSV data."""

    output_path = (
        DATA_DIRECTORY
        / "day18_portfolio_samples.csv"
    )

    ranked_results = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "portfolio_abcd",
                "selected_assets",
                "count",
                "probability",
            ]
        )

        for bits, count in ranked_results:
            writer.writerow(
                [
                    bits,
                    selected_assets(bits),
                    count,
                    count / SHOTS,
                ]
            )

    return output_path


def save_report(
    circuit: QuantumCircuit,
    counts: dict[str, int],
) -> Path:
    """Save a readable Day 18 experiment report."""

    output_path = (
        REPORT_DIRECTORY
        / "day18_quantum_finance_report.txt"
    )

    ranked_results = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    most_sampled_bits, most_sampled_count = ranked_results[0]

    report_lines = [
        "PROJECT-Q Day 18 - Quantum Finance Lab",
        "=" * 48,
        "",
        "Objective",
        "---------",
        "Use four qubits to represent four investment choices",
        "and sample candidate portfolios from a parameterized",
        "quantum circuit.",
        "",
        "Important limitation",
        "--------------------",
        "This lab samples candidate portfolios.",
        "It does not yet perform full QAOA or VQE optimization.",
        "",
        "Asset Mapping",
        "-------------",
        "q0 = Asset A",
        "q1 = Asset B",
        "q2 = Asset C",
        "q3 = Asset D",
        "",
        "Portfolio strings are displayed in A-B-C-D order.",
        "",
        "Rotation Angles",
        "---------------",
        f"Asset A: {ROTATION_ANGLES[0]} radians",
        f"Asset B: {ROTATION_ANGLES[1]} radians",
        f"Asset C: {ROTATION_ANGLES[2]} radians",
        f"Asset D: {ROTATION_ANGLES[3]} radians",
        "",
        "Shots",
        "-----",
        str(SHOTS),
        "",
        "Most Frequently Sampled Portfolio",
        "---------------------------------",
        f"Portfolio: {most_sampled_bits}",
        f"Selected assets: {selected_assets(most_sampled_bits)}",
        f"Count: {most_sampled_count}/{SHOTS}",
        (
            "Sampling probability: "
            f"{most_sampled_count / SHOTS:.2%}"
        ),
        "",
        "All Measured Portfolios",
        "-----------------------",
    ]

    for bits, count in ranked_results:
        report_lines.append(
            f"{bits}: count={count}, "
            f"probability={count / SHOTS:.2%}, "
            f"assets={selected_assets(bits)}"
        )

    report_lines.extend(
        [
            "",
            "Validation",
            "----------",
            (
                "PASS: Measurement counts equal "
                f"{SHOTS} requested shots."
            ),
            (
                "PASS: Every measured result is a valid "
                "four-bit portfolio."
            ),
            "",
            "Workflow",
            "--------",
            "1. Create four investment qubits.",
            "2. Apply Hadamard gates to prepare candidate portfolios.",
            "3. Apply parameterized RY rotation gates.",
            "4. Measure the four-qubit circuit.",
            "5. Convert Qiskit output into Asset A-B-C-D order.",
            "6. Rank portfolios by their sampling frequency.",
            "",
            "Circuit",
            "-------",
            str(circuit.draw(output="text")),
            "",
            "Disclaimer",
            "----------",
            "This is an educational quantum computing demonstration.",
            "It is not financial or investment advice.",
        ]
    )

    output_path.write_text(
        "\n".join(report_lines),
        encoding="utf-8",
    )

    return output_path


def run_lab() -> None:
    """Run and validate the complete Day 18 lab."""

    circuit = build_quantum_finance_circuit()

    sampler = StatevectorSampler(seed=SEED)

    job = sampler.run(
        [circuit],
        shots=SHOTS,
    )

    result = job.result()

    raw_counts = result[0].data.meas.get_counts()

    counts = convert_to_asset_order(raw_counts)

    total_counts = sum(counts.values())

    if total_counts != SHOTS:
        raise RuntimeError(
            f"Expected {SHOTS} measurements, "
            f"but received {total_counts}."
        )

    for bits in counts:
        if len(bits) != 4 or any(
            bit not in "01"
            for bit in bits
        ):
            raise RuntimeError(
                f"Invalid portfolio bitstring: {bits}"
            )

    ranked_results = sorted(
        counts.items(),
        key=lambda item: (-item[1], item[0]),
    )

    most_sampled_bits, most_sampled_count = ranked_results[0]

    histogram_path = save_histogram(counts)
    circuit_path = save_circuit_image(circuit)
    csv_path = save_csv(counts)
    report_path = save_report(circuit, counts)

    print()
    print("PROJECT-Q DAY 18 - QUANTUM FINANCE")
    print("=" * 48)
    print(f"Qubits:              4")
    print(f"Possible portfolios: 16")
    print(f"Shots:               {SHOTS}")
    print(
        f"Observed portfolios: {len(counts)}/16"
    )

    print()
    print("MOST FREQUENTLY SAMPLED PORTFOLIO")
    print("-" * 48)
    print(f"Portfolio:           {most_sampled_bits}")
    print(
        "Selected assets:     "
        f"{selected_assets(most_sampled_bits)}"
    )
    print(
        f"Count:               "
        f"{most_sampled_count}/{SHOTS}"
    )
    print(
        f"Probability:         "
        f"{most_sampled_count / SHOTS:.2%}"
    )

    print()
    print("TOP FIVE PORTFOLIOS")
    print("-" * 48)

    for position, (bits, count) in enumerate(
        ranked_results[:5],
        start=1,
    ):
        print(
            f"{position}. {bits} | "
            f"{selected_assets(bits)} | "
            f"{count} samples | "
            f"{count / SHOTS:.2%}"
        )

    print()
    print("VALIDATION")
    print("-" * 48)
    print(
        f"PASS: Measurement counts equal {SHOTS} shots."
    )
    print(
        "PASS: All measured portfolios contain four binary values."
    )
    print(
        "PASS: Qiskit bit order was converted to A-B-C-D order."
    )

    print()
    print("SAVED LAB ARTIFACTS")
    print("-" * 48)
    print(f"Report:    {report_path}")
    print(f"Histogram: {histogram_path}")
    print(f"Circuit:   {circuit_path}")
    print(f"CSV data:  {csv_path}")


if __name__ == "__main__":
    run_lab()