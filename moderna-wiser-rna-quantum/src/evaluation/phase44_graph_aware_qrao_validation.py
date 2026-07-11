from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any, Dict, List, Set

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

TABLE_DIR = ROOT / "results" / "publication_tables"
FIGURE_DIR = ROOT / "results" / "publication_figures"
DOCS_DIR = ROOT / "docs"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

SUMMARY_TABLE = TABLE_DIR / "graph_aware_qrao_summary.csv"
MAPPING_TABLE = TABLE_DIR / "graph_aware_qrao_mapping.csv"
CONFLICT_TABLE = TABLE_DIR / "graph_aware_qrao_conflict_check.csv"

QUBIT_REDUCTION_FIGURE = FIGURE_DIR / "graph_aware_qrao_qubit_reduction.png"
COLORING_COUNTS_FIGURE = FIGURE_DIR / "graph_aware_qrao_coloring_counts.png"

PHASE44_DOC = DOCS_DIR / "phase44_graph_aware_qrao_validation.md"
RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"

PHASE44_MARKER = "<!-- PHASE44_GRAPH_AWARE_QRAO_VALIDATION -->"

PAULI_2_TO_1 = ["X", "Z"]
PAULI_3_TO_1 = ["X", "Y", "Z"]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames: List[str] = []

    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except ValueError:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def normalize_variable_name(value: Any) -> str:
    text = str(value or "").strip()

    if text.startswith("x_"):
        return text

    if text.isdigit():
        return f"x_{text}"

    return text


def load_interaction_graph() -> Dict[str, Dict[str, Any]]:
    trace_rows = read_csv(TABLE_DIR / "stem_traceability_table.csv")
    ising_rows = read_csv(TABLE_DIR / "qubo_to_ising_coefficients.csv")
    exact_rows = read_csv(TABLE_DIR / "exact_validation_results.csv")

    sequence_lengths = {
        row.get("sequence_id", ""): safe_int(row.get("length"))
        for row in exact_rows
    }

    graphs: Dict[str, Dict[str, Any]] = {}

    for row in trace_rows:
        sequence_id = row.get("sequence_id", "")
        variable = normalize_variable_name(row.get("variable"))

        if not sequence_id or not variable:
            continue

        graph = graphs.setdefault(
            sequence_id,
            {
                "sequence_id": sequence_id,
                "sequence_length": sequence_lengths.get(sequence_id, 0),
                "vertices": set(),
                "edges": set(),
                "variable_metadata": {},
            },
        )

        graph["vertices"].add(variable)
        graph["variable_metadata"][variable] = {
            "stem_length": row.get("stem_length", ""),
            "linear_coefficient": row.get("linear_coefficient", ""),
            "stem_score": row.get("stem_score", ""),
            "stem_pairs_1_based": row.get("stem_pairs_1_based", ""),
            "stem_pair_labels": row.get("stem_pair_labels", ""),
        }

    for row in ising_rows:
        sequence_id = row.get("sequence_id", "")
        coefficient_type = row.get("coefficient_type", "")
        term = row.get("term", "")

        if coefficient_type != "coupling":
            continue

        if not sequence_id or not term.startswith("J_"):
            continue

        parts = term.replace("J_", "").split("_")

        if len(parts) != 2:
            continue

        left = normalize_variable_name(parts[0])
        right = normalize_variable_name(parts[1])

        if left == right:
            continue

        graph = graphs.setdefault(
            sequence_id,
            {
                "sequence_id": sequence_id,
                "sequence_length": sequence_lengths.get(sequence_id, 0),
                "vertices": set(),
                "edges": set(),
                "variable_metadata": {},
            },
        )

        graph["vertices"].add(left)
        graph["vertices"].add(right)
        graph["edges"].add(tuple(sorted((left, right))))

    return graphs


def adjacency_from_graph(vertices: Set[str], edges: Set[tuple[str, str]]) -> Dict[str, Set[str]]:
    adjacency = {vertex: set() for vertex in vertices}

    for left, right in edges:
        adjacency.setdefault(left, set()).add(right)
        adjacency.setdefault(right, set()).add(left)

    return adjacency


def greedy_coloring(vertices: Set[str], edges: Set[tuple[str, str]]) -> Dict[str, int]:
    adjacency = adjacency_from_graph(vertices, edges)

    ordered_vertices = sorted(
        vertices,
        key=lambda vertex: (-len(adjacency.get(vertex, set())), vertex),
    )

    coloring: Dict[str, int] = {}

    for vertex in ordered_vertices:
        used_neighbor_colors = {
            coloring[neighbor]
            for neighbor in adjacency.get(vertex, set())
            if neighbor in coloring
        }

        color = 0

        while color in used_neighbor_colors:
            color += 1

        coloring[vertex] = color

    return coloring


def pack_by_color(
    coloring: Dict[str, int],
    capacity: int,
    pauli_labels: List[str],
) -> Dict[str, Dict[str, Any]]:
    color_groups: Dict[int, List[str]] = {}

    for variable, color in coloring.items():
        color_groups.setdefault(color, []).append(variable)

    mapping: Dict[str, Dict[str, Any]] = {}
    qubit_index = 0

    for color in sorted(color_groups):
        variables = sorted(color_groups[color])

        for start in range(0, len(variables), capacity):
            chunk = variables[start : start + capacity]

            for slot, variable in enumerate(chunk):
                mapping[variable] = {
                    "qrao_color": color,
                    "compressed_qubit": f"q_{qubit_index}",
                    "pauli_axis": pauli_labels[slot],
                    "slot": slot,
                    "capacity": capacity,
                }

            qubit_index += 1

    return mapping


def check_mapping_conflicts(
    sequence_id: str,
    edges: Set[tuple[str, str]],
    mapping: Dict[str, Dict[str, Any]],
    strategy: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for left, right in sorted(edges):
        left_qubit = mapping.get(left, {}).get("compressed_qubit", "")
        right_qubit = mapping.get(right, {}).get("compressed_qubit", "")
        conflict = left_qubit != "" and left_qubit == right_qubit

        rows.append(
            {
                "sequence_id": sequence_id,
                "strategy": strategy,
                "variable_i": left,
                "variable_j": right,
                "qubit_i": left_qubit,
                "qubit_j": right_qubit,
                "same_qubit_conflict": conflict,
                "check_note": "Interacting variables should not share a compressed qubit.",
            }
        )

    return rows


def mapping_rows_for_strategy(
    sequence_id: str,
    graph: Dict[str, Any],
    coloring: Dict[str, int],
    mapping: Dict[str, Dict[str, Any]],
    strategy: str,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    metadata = graph.get("variable_metadata", {})

    for variable in sorted(graph["vertices"]):
        info = mapping.get(variable, {})
        variable_meta = metadata.get(variable, {})

        rows.append(
            {
                "sequence_id": sequence_id,
                "strategy": strategy,
                "variable": variable,
                "qrao_color": coloring.get(variable, ""),
                "compressed_qubit": info.get("compressed_qubit", ""),
                "pauli_axis": info.get("pauli_axis", ""),
                "slot": info.get("slot", ""),
                "capacity": info.get("capacity", ""),
                "stem_length": variable_meta.get("stem_length", ""),
                "linear_coefficient": variable_meta.get("linear_coefficient", ""),
                "stem_score": variable_meta.get("stem_score", ""),
                "stem_pairs_1_based": variable_meta.get("stem_pairs_1_based", ""),
                "stem_pair_labels": variable_meta.get("stem_pair_labels", ""),
            }
        )

    return rows


def generic_qubits(variable_count: int, capacity: int) -> int:
    if variable_count <= 0:
        return 0

    return math.ceil(variable_count / capacity)


def graph_aware_qubits(mapping: Dict[str, Dict[str, Any]]) -> int:
    qubits = {
        info["compressed_qubit"]
        for info in mapping.values()
        if info.get("compressed_qubit")
    }

    return len(qubits)


def reduction_percent(direct_qubits: int, compressed_qubits: int) -> float:
    if direct_qubits <= 0:
        return 0.0

    return round(100.0 * (direct_qubits - compressed_qubits) / direct_qubits, 3)


def build_phase44_outputs() -> None:
    graphs = load_interaction_graph()

    summary_rows: List[Dict[str, Any]] = []
    mapping_rows: List[Dict[str, Any]] = []
    conflict_rows: List[Dict[str, Any]] = []

    for sequence_id, graph in sorted(graphs.items()):
        vertices: Set[str] = graph["vertices"]
        edges: Set[tuple[str, str]] = graph["edges"]
        coloring = greedy_coloring(vertices, edges)

        variable_count = len(vertices)
        edge_count = len(edges)
        color_count = len(set(coloring.values())) if coloring else 0
        direct_qubits = variable_count

        mapping_2 = pack_by_color(coloring, capacity=2, pauli_labels=PAULI_2_TO_1)
        mapping_3 = pack_by_color(coloring, capacity=3, pauli_labels=PAULI_3_TO_1)

        graph_aware_2 = graph_aware_qubits(mapping_2)
        graph_aware_3 = graph_aware_qubits(mapping_3)

        generic_2 = generic_qubits(variable_count, 2)
        generic_3 = generic_qubits(variable_count, 3)

        conflict_2 = check_mapping_conflicts(sequence_id, edges, mapping_2, "graph_aware_2_to_1")
        conflict_3 = check_mapping_conflicts(sequence_id, edges, mapping_3, "graph_aware_3_to_1")

        conflict_rows.extend(conflict_2)
        conflict_rows.extend(conflict_3)

        conflict_count_2 = sum(1 for row in conflict_2 if row["same_qubit_conflict"])
        conflict_count_3 = sum(1 for row in conflict_3 if row["same_qubit_conflict"])

        mapping_rows.extend(mapping_rows_for_strategy(sequence_id, graph, coloring, mapping_2, "graph_aware_2_to_1"))
        mapping_rows.extend(mapping_rows_for_strategy(sequence_id, graph, coloring, mapping_3, "graph_aware_3_to_1"))

        summary_rows.append(
            {
                "sequence_id": sequence_id,
                "sequence_length": graph.get("sequence_length", ""),
                "variable_count": variable_count,
                "interaction_edge_count": edge_count,
                "qrao_color_count": color_count,
                "direct_qubits": direct_qubits,
                "generic_2_to_1_qubits": generic_2,
                "generic_3_to_1_qubits": generic_3,
                "graph_aware_2_to_1_qubits": graph_aware_2,
                "graph_aware_3_to_1_qubits": graph_aware_3,
                "generic_2_to_1_reduction_percent": reduction_percent(direct_qubits, generic_2),
                "generic_3_to_1_reduction_percent": reduction_percent(direct_qubits, generic_3),
                "graph_aware_2_to_1_reduction_percent": reduction_percent(direct_qubits, graph_aware_2),
                "graph_aware_3_to_1_reduction_percent": reduction_percent(direct_qubits, graph_aware_3),
                "graph_aware_2_to_1_conflicts": conflict_count_2,
                "graph_aware_3_to_1_conflicts": conflict_count_3,
                "validation_status": "pass" if conflict_count_2 == 0 and conflict_count_3 == 0 else "check_required",
                "interpretation": "Graph-aware QRAO packing avoids assigning interacting QUBO variables to the same compressed qubit.",
            }
        )

    write_csv(SUMMARY_TABLE, summary_rows)
    write_csv(MAPPING_TABLE, mapping_rows)
    write_csv(CONFLICT_TABLE, conflict_rows)

    plot_qubit_reduction(summary_rows)
    plot_coloring_counts(summary_rows)
    write_phase44_doc(summary_rows)
    update_results_summary()
    update_project_navigation()


def plot_qubit_reduction(summary_rows: List[Dict[str, Any]]) -> None:
    labels = [row["sequence_id"].replace("EXACT_", "E") for row in summary_rows]
    direct = [safe_float(row["direct_qubits"]) for row in summary_rows]
    graph_2 = [safe_float(row["graph_aware_2_to_1_qubits"]) for row in summary_rows]
    graph_3 = [safe_float(row["graph_aware_3_to_1_qubits"]) for row in summary_rows]

    x_positions = list(range(len(labels)))
    width = 0.25

    plt.figure(figsize=(11, 5))
    plt.bar([x - width for x in x_positions], direct, width, label="Direct")
    plt.bar(x_positions, graph_2, width, label="Graph-aware 2-to-1")
    plt.bar([x + width for x in x_positions], graph_3, width, label="Graph-aware 3-to-1")
    plt.title("Graph-Aware QRAO Qubit Requirement")
    plt.xlabel("RNA Exact-Validation Sequence")
    plt.ylabel("Qubits Required")
    plt.xticks(x_positions, labels, rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(QUBIT_REDUCTION_FIGURE, dpi=250)
    plt.close()


def plot_coloring_counts(summary_rows: List[Dict[str, Any]]) -> None:
    labels = [row["sequence_id"].replace("EXACT_", "E") for row in summary_rows]
    colors = [safe_float(row["qrao_color_count"]) for row in summary_rows]
    edges = [safe_float(row["interaction_edge_count"]) for row in summary_rows]

    x_positions = list(range(len(labels)))
    width = 0.3

    plt.figure(figsize=(11, 5))
    plt.bar([x - width / 2 for x in x_positions], colors, width, label="QRAO colors")
    plt.bar([x + width / 2 for x in x_positions], edges, width, label="Interaction edges")
    plt.title("QUBO Interaction Graph Coloring Summary")
    plt.xlabel("RNA Exact-Validation Sequence")
    plt.ylabel("Count")
    plt.xticks(x_positions, labels, rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(COLORING_COUNTS_FIGURE, dpi=250)
    plt.close()


def append_once(path: Path, marker: str, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = ""

    if marker in existing:
        return

    updated = existing.rstrip() + "\n\n" + marker + "\n" + content.strip() + "\n"
    path.write_text(updated, encoding="utf-8")


def write_phase44_doc(summary_rows: List[Dict[str, Any]]) -> None:
    total_sequences = len(summary_rows)
    passing_rows = sum(1 for row in summary_rows if row["validation_status"] == "pass")

    lines = [
        "# Phase 44 — Graph-Aware QRAO Compression Validation",
        "",
        "## Purpose",
        "",
        "Phase 44 upgrades the qubit-compression layer by using the QUBO interaction graph instead of only estimating compression by variable count.",
        "",
        "## Research Motivation",
        "",
        "In QRAO-style compression, interacting QUBO variables should not be packed into the same compressed qubit under the standard QRAC/QRAO construction.",
        "",
        "Therefore, the QUBO interaction graph is part of the encoding process, not just a visualization.",
        "",
        "## Method",
        "",
        "For each exact-validation sequence:",
        "",
        "1. Build a QUBO interaction graph.",
        "2. Treat each binary variable as a graph vertex.",
        "3. Treat each nonzero quadratic QUBO/Ising coupling as an edge.",
        "4. Apply greedy graph coloring.",
        "5. Pack variables within color classes into 2-to-1 and 3-to-1 QRAO-style groups.",
        "6. Verify that interacting variables do not share a compressed qubit.",
        "",
        "## Generated Tables",
        "",
        "- `results/publication_tables/graph_aware_qrao_summary.csv`",
        "- `results/publication_tables/graph_aware_qrao_mapping.csv`",
        "- `results/publication_tables/graph_aware_qrao_conflict_check.csv`",
        "",
        "## Generated Figures",
        "",
        "- `results/publication_figures/graph_aware_qrao_qubit_reduction.png`",
        "- `results/publication_figures/graph_aware_qrao_coloring_counts.png`",
        "",
        "## Summary",
        "",
        f"- Sequences analyzed: {total_sequences}",
        f"- Sequences passing no-same-qubit conflict checks: {passing_rows}",
        "",
        "## Safe Interpretation",
        "",
        "This phase validates graph-aware packing logic for QRAO-style compression.",
        "",
        "It does not prove that compression improves RNA folding accuracy.",
        "",
        "Future work must compare rounded compressed solutions against exact QUBO optima and biological reference structures.",
    ]

    PHASE44_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_results_summary() -> None:
    content = """
# Phase 44 Update — Graph-Aware QRAO Compression Validation

Phase 44 upgraded the compression layer by using the QUBO interaction graph.

The project now compares direct qubit mapping with graph-aware 2-to-1 and 3-to-1 QRAO-style mappings. The key rule is that interacting QUBO variables should not be packed into the same compressed qubit.

Generated outputs include a graph-aware QRAO summary table, mapping table, conflict-check table, qubit-reduction figure, and coloring-count figure.

Safe interpretation:

This validates the compression mapping logic. It does not yet prove that compression preserves RNA solution quality after rounding.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE44_MARKER, content)


def update_project_navigation() -> None:
    content = """
# Phase 44 — Graph-Aware QRAO Compression Validation

Purpose:

Upgrade the QRAO compression layer so it uses the QUBO interaction graph.

Main file:

`src/evaluation/phase44_graph_aware_qrao_validation.py`

Generated files:

`results/publication_tables/graph_aware_qrao_summary.csv`  
`results/publication_tables/graph_aware_qrao_mapping.csv`  
`results/publication_tables/graph_aware_qrao_conflict_check.csv`  
`results/publication_figures/graph_aware_qrao_qubit_reduction.png`  
`results/publication_figures/graph_aware_qrao_coloring_counts.png`  
`docs/phase44_graph_aware_qrao_validation.md`

Run:

`python src\\evaluation\\phase44_graph_aware_qrao_validation.py`

Safe interpretation:

Graph-aware QRAO validates compression mapping logic, but it does not yet prove compressed solutions preserve RNA folding quality.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE44_MARKER, content)


def main() -> None:
    build_phase44_outputs()

    print("Phase 44 graph-aware QRAO compression validation complete.")
    print(f"Summary table: {SUMMARY_TABLE}")
    print(f"Mapping table: {MAPPING_TABLE}")
    print(f"Conflict check table: {CONFLICT_TABLE}")
    print(f"Qubit reduction figure: {QUBIT_REDUCTION_FIGURE}")
    print(f"Coloring counts figure: {COLORING_COUNTS_FIGURE}")
    print(f"Documentation: {PHASE44_DOC}")


if __name__ == "__main__":
    main()