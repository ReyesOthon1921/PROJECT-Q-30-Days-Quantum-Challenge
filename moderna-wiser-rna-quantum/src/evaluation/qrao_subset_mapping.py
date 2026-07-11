"""
qrao_subset_mapping.py

Phase 35 — QRAO Subset Mapping.

This module creates a simple QRAO-style variable-to-qubit mapping for
RNA QUBO variables.

Important:
This is not a full QRAO solver. It creates a research mapping layer
that assigns multiple binary variables to one compressed qubit using
Pauli-axis labels.

Standard QRAO / QRAC layer:
- 2-to-1 or 3-to-1 style compression estimates.
- This file implements a 3-to-1 X/Y/Z mapping.

Separate from this:
- Qubit-efficient log encoding can estimate many variables with fewer qubits,
  such as 64 variables -> 7 qubits, but that is not the same as standard QRAO.
"""

import math
import os
import time

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo


DEFAULT_OUTPUT_DIR = "static/outputs"


def save_bar_chart(title, labels, values, ylabel, output_path):
    plt.figure(figsize=(10, 5.8))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=25, ha="right")
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def build_3_to_1_qrao_mapping(variable_names: list[str]) -> list[dict]:
    """
    Assign up to three binary variables to one compressed qubit.

    The three variables are assigned to Pauli axes:

    variable 0 -> X
    variable 1 -> Y
    variable 2 -> Z

    Then the pattern repeats for the next compressed qubit.
    """
    axes = ["X", "Y", "Z"]
    mapping = []

    for index, variable in enumerate(variable_names):
        compressed_qubit = index // 3
        pauli_axis = axes[index % 3]

        mapping.append(
            {
                "variable": variable,
                "compressed_qubit": compressed_qubit,
                "pauli_axis": pauli_axis,
                "encoding": f"qubit_{compressed_qubit}_{pauli_axis}",
            }
        )

    return mapping


def build_2_to_1_qrao_mapping(variable_names: list[str]) -> list[dict]:
    """
    Assign up to two binary variables to one compressed qubit.

    This is a lower-compression QRAO-style mapping.
    """
    axes = ["X", "Z"]
    mapping = []

    for index, variable in enumerate(variable_names):
        compressed_qubit = index // 2
        pauli_axis = axes[index % 2]

        mapping.append(
            {
                "variable": variable,
                "compressed_qubit": compressed_qubit,
                "pauli_axis": pauli_axis,
                "encoding": f"qubit_{compressed_qubit}_{pauli_axis}",
            }
        )

    return mapping


def group_mapping_by_qubit(mapping: list[dict]) -> dict:
    qubit_groups = {}

    for item in mapping:
        qubit_key = f"compressed_qubit_{item['compressed_qubit']}"

        if qubit_key not in qubit_groups:
            qubit_groups[qubit_key] = []

        qubit_groups[qubit_key].append(
            {
                "variable": item["variable"],
                "pauli_axis": item["pauli_axis"],
                "encoding": item["encoding"],
            }
        )

    return qubit_groups


def count_axes(mapping: list[dict]) -> dict:
    axis_counts = {}

    for item in mapping:
        axis = item["pauli_axis"]

        if axis not in axis_counts:
            axis_counts[axis] = 0

        axis_counts[axis] += 1

    return axis_counts


def run_qrao_subset_mapping(sequence: str, max_variables: int = 18, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    start = time.perf_counter()

    cleaned = clean_sequence(sequence)
    os.makedirs(output_dir, exist_ok=True)

    qubo = build_stem_qubo(cleaned)

    variable_names = list(qubo.get("linear_terms", {}).keys())
    selected_variables = variable_names[:max_variables]

    direct_qubits = len(selected_variables)

    two_to_one_mapping = build_2_to_1_qrao_mapping(selected_variables)
    three_to_one_mapping = build_3_to_1_qrao_mapping(selected_variables)

    two_to_one_qubits = math.ceil(len(selected_variables) / 2) if selected_variables else 0
    three_to_one_qubits = math.ceil(len(selected_variables) / 3) if selected_variables else 0

    two_to_one_ratio = round(direct_qubits / two_to_one_qubits, 4) if two_to_one_qubits else 0.0
    three_to_one_ratio = round(direct_qubits / three_to_one_qubits, 4) if three_to_one_qubits else 0.0

    three_to_one_groups = group_mapping_by_qubit(three_to_one_mapping)
    three_to_one_axis_counts = count_axes(three_to_one_mapping)

    qubit_graph_path = os.path.join(output_dir, "qrao_subset_mapping_qubits.png")
    save_bar_chart(
        title="QRAO Subset Mapping: Direct vs Compressed Qubits",
        labels=["Direct", "2-to-1 QRAC", "3-to-1 QRAC"],
        values=[direct_qubits, two_to_one_qubits, three_to_one_qubits],
        ylabel="Qubits",
        output_path=qubit_graph_path,
    )

    axis_graph_path = os.path.join(output_dir, "qrao_subset_mapping_axes.png")
    save_bar_chart(
        title="QRAO 3-to-1 Mapping: Pauli Axis Assignments",
        labels=list(three_to_one_axis_counts.keys()),
        values=list(three_to_one_axis_counts.values()),
        ylabel="Variable count",
        output_path=axis_graph_path,
    )

    ratio_graph_path = os.path.join(output_dir, "qrao_subset_mapping_ratio.png")
    save_bar_chart(
        title="QRAO Subset Mapping: Compression Ratio",
        labels=["2-to-1 QRAC", "3-to-1 QRAC"],
        values=[two_to_one_ratio, three_to_one_ratio],
        ylabel="Compression ratio vs direct",
        output_path=ratio_graph_path,
    )

    generated_graphs = [
        {
            "key": "qrao_qubits",
            "title": "QRAO Subset Mapping: Direct vs Compressed Qubits",
            "filename": "qrao_subset_mapping_qubits.png",
            "static_path": "/static/outputs/qrao_subset_mapping_qubits.png",
        },
        {
            "key": "qrao_axes",
            "title": "QRAO 3-to-1 Mapping: Pauli Axis Assignments",
            "filename": "qrao_subset_mapping_axes.png",
            "static_path": "/static/outputs/qrao_subset_mapping_axes.png",
        },
        {
            "key": "qrao_ratio",
            "title": "QRAO Subset Mapping: Compression Ratio",
            "filename": "qrao_subset_mapping_ratio.png",
            "static_path": "/static/outputs/qrao_subset_mapping_ratio.png",
        },
    ]

    total_runtime_seconds = round(time.perf_counter() - start, 4)

    return {
        "success": True,
        "phase": "Phase 35 — QRAO Subset Mapping",
        "sequence": cleaned,
        "selected_variable_count": len(selected_variables),
        "direct_qubits": direct_qubits,
        "two_to_one_qubits": two_to_one_qubits,
        "three_to_one_qubits": three_to_one_qubits,
        "two_to_one_compression_ratio": two_to_one_ratio,
        "three_to_one_compression_ratio": three_to_one_ratio,
        "two_to_one_mapping": two_to_one_mapping,
        "three_to_one_mapping": three_to_one_mapping,
        "three_to_one_qubit_groups": three_to_one_groups,
        "three_to_one_axis_counts": three_to_one_axis_counts,
        "generated_graph_count": len(generated_graphs),
        "generated_graphs": generated_graphs,
        "total_runtime_seconds": total_runtime_seconds,
        "research_note": (
            "This is a QRAO-style variable mapping layer. It assigns binary RNA stem variables "
            "to compressed qubits using Pauli-axis labels. The 3-to-1 version maps variables to X, Y, and Z axes. "
            "This is not a full QRAO solver."
        ),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_qrao_subset_mapping(sequence)

    print("QRAO subset mapping summary")
    print("---------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"selected_variable_count: {result['selected_variable_count']}")
    print(f"direct_qubits: {result['direct_qubits']}")
    print(f"2-to-1 compressed qubits: {result['two_to_one_qubits']}")
    print(f"3-to-1 compressed qubits: {result['three_to_one_qubits']}")
    print(f"2-to-1 compression ratio: {result['two_to_one_compression_ratio']}")
    print(f"3-to-1 compression ratio: {result['three_to_one_compression_ratio']}")
    print(f"total_runtime_seconds: {result['total_runtime_seconds']}")

    print("first 3-to-1 mappings:")
    for item in result["three_to_one_mapping"][:12]:
        print(f"- {item['variable']} -> qubit {item['compressed_qubit']} axis {item['pauli_axis']}")

    print("generated graphs:")
    for graph in result["generated_graphs"]:
        print(f"- {graph['title']}: {graph['static_path']}")