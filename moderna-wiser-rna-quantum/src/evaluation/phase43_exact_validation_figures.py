from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

TABLE_DIR = ROOT / "results" / "publication_tables"
FIGURE_DIR = ROOT / "results" / "publication_figures"
DOCS_DIR = ROOT / "docs"

FIGURE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

EXACT_RESULTS_TABLE = TABLE_DIR / "exact_validation_results.csv"
ENERGY_AUDIT_SUMMARY_TABLE = TABLE_DIR / "qubo_energy_audit_summary.csv"
ISING_COEFFICIENTS_TABLE = TABLE_DIR / "qubo_to_ising_coefficients.csv"
INTEGRATED_SUMMARY_TABLE = TABLE_DIR / "exact_validation_integrated_summary.csv"

EXACT_MIN_ENERGY_FIGURE = FIGURE_DIR / "exact_minimum_energy.png"
ASSIGNMENT_GROWTH_FIGURE = FIGURE_DIR / "exact_assignment_growth.png"
ENERGY_DECOMPOSITION_FIGURE = FIGURE_DIR / "exact_energy_decomposition.png"
ISING_COUNTS_FIGURE = FIGURE_DIR / "ising_coefficient_counts.png"

PHASE43_DOC = DOCS_DIR / "phase43_exact_validation_figures.md"
RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"

PHASE43_MARKER = "<!-- PHASE43_EXACT_VALIDATION_FIGURES -->"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or str(value).strip() == "":
            return default
        return float(value)
    except ValueError:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or str(value).strip() == "":
            return default
        return int(float(value))
    except ValueError:
        return default


def sequence_labels(rows: List[Dict[str, str]]) -> List[str]:
    labels: List[str] = []

    for row in rows:
        sequence_id = row.get("sequence_id", "")

        if sequence_id:
            labels.append(sequence_id.replace("EXACT_", "E"))
        else:
            labels.append(f"seq_{len(labels) + 1}")

    return labels


def save_bar_chart(
    labels: List[str],
    values: List[float],
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title(title)
    plt.xlabel("RNA Test Sequence")
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=250)
    plt.close()


def plot_exact_minimum_energy(exact_rows: List[Dict[str, str]]) -> None:
    labels = sequence_labels(exact_rows)
    values = [
        safe_float(row.get("exact_minimum_energy"))
        for row in exact_rows
    ]

    save_bar_chart(
        labels=labels,
        values=values,
        title="Exact Minimum QUBO Energy by RNA Sequence",
        ylabel="Exact Minimum Energy",
        output_path=EXACT_MIN_ENERGY_FIGURE,
    )


def plot_assignment_growth(exact_rows: List[Dict[str, str]]) -> None:
    labels = sequence_labels(exact_rows)
    values = [
        safe_int(row.get("assignment_count"))
        for row in exact_rows
    ]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title("Exact Enumeration Assignment Growth")
    plt.xlabel("RNA Test Sequence")
    plt.ylabel("Number of Bitstring Assignments")
    plt.yscale("log")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(ASSIGNMENT_GROWTH_FIGURE, dpi=250)
    plt.close()


def plot_energy_decomposition(energy_rows: List[Dict[str, str]]) -> None:
    labels = sequence_labels(energy_rows)

    linear_values = [
        safe_float(row.get("linear_energy"))
        for row in energy_rows
    ]

    overlap_values = [
        safe_float(row.get("overlap_penalty_energy"))
        for row in energy_rows
    ]

    crossing_values = [
        safe_float(row.get("crossing_penalty_energy"))
        for row in energy_rows
    ]

    interaction_values = [
        safe_float(row.get("interaction_energy"))
        for row in energy_rows
    ]

    x_positions = list(range(len(labels)))
    width = 0.2

    plt.figure(figsize=(11, 5))
    plt.bar([x - 1.5 * width for x in x_positions], linear_values, width, label="Linear energy")
    plt.bar([x - 0.5 * width for x in x_positions], overlap_values, width, label="Overlap penalty")
    plt.bar([x + 0.5 * width for x in x_positions], crossing_values, width, label="Crossing penalty")
    plt.bar([x + 1.5 * width for x in x_positions], interaction_values, width, label="Interaction energy")

    plt.title("QUBO Energy Decomposition for Exact Optima")
    plt.xlabel("RNA Test Sequence")
    plt.ylabel("Energy Contribution")
    plt.xticks(x_positions, labels, rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ENERGY_DECOMPOSITION_FIGURE, dpi=250)
    plt.close()


def group_ising_counts(ising_rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, Dict[str, Any]] = {}

    for row in ising_rows:
        sequence_id = row.get("sequence_id", "")

        if not sequence_id:
            continue

        group = grouped.setdefault(
            sequence_id,
            {
                "sequence_id": sequence_id,
                "constant_offset_count": 0,
                "linear_field_count": 0,
                "coupling_count": 0,
            },
        )

        coefficient_type = row.get("coefficient_type", "")

        if coefficient_type == "constant_offset":
            group["constant_offset_count"] += 1
        elif coefficient_type == "linear_field":
            group["linear_field_count"] += 1
        elif coefficient_type == "coupling":
            group["coupling_count"] += 1

    return list(grouped.values())


def plot_ising_coefficient_counts(ising_rows: List[Dict[str, str]]) -> None:
    grouped = group_ising_counts(ising_rows)

    labels = [
        row["sequence_id"].replace("EXACT_", "E")
        for row in grouped
    ]

    constant_values = [
        row["constant_offset_count"]
        for row in grouped
    ]

    linear_values = [
        row["linear_field_count"]
        for row in grouped
    ]

    coupling_values = [
        row["coupling_count"]
        for row in grouped
    ]

    x_positions = list(range(len(labels)))
    width = 0.25

    plt.figure(figsize=(11, 5))
    plt.bar([x - width for x in x_positions], constant_values, width, label="Constant offsets")
    plt.bar(x_positions, linear_values, width, label="Linear fields h")
    plt.bar([x + width for x in x_positions], coupling_values, width, label="Couplings J")

    plt.title("QUBO-to-Ising Coefficient Counts")
    plt.xlabel("RNA Test Sequence")
    plt.ylabel("Coefficient Count")
    plt.xticks(x_positions, labels, rotation=30, ha="right")
    plt.legend()
    plt.tight_layout()
    plt.savefig(ISING_COUNTS_FIGURE, dpi=250)
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


def write_phase43_doc(
    exact_rows: List[Dict[str, str]],
    energy_rows: List[Dict[str, str]],
    ising_rows: List[Dict[str, str]],
) -> None:
    total_assignments = sum(
        safe_int(row.get("assignment_count"))
        for row in exact_rows
    )

    min_energies = [
        safe_float(row.get("exact_minimum_energy"))
        for row in exact_rows
    ]

    best_energy: Optional[float] = min(min_energies) if min_energies else None
    worst_energy: Optional[float] = max(min_energies) if min_energies else None

    grouped_ising = group_ising_counts(ising_rows)
    total_h_fields = sum(row["linear_field_count"] for row in grouped_ising)
    total_j_couplings = sum(row["coupling_count"] for row in grouped_ising)

    lines = [
        "# Phase 43 — Exact Validation Publication Figures",
        "",
        "## Purpose",
        "",
        "Phase 43 converts the exact-validation tables into publication-ready figures.",
        "",
        "The goal is to make the exact-validation layer easier to interpret visually for the paper, dashboard, and professor review.",
        "",
        "## Input Tables",
        "",
        "- `results/publication_tables/exact_validation_results.csv`",
        "- `results/publication_tables/qubo_energy_audit_summary.csv`",
        "- `results/publication_tables/qubo_to_ising_coefficients.csv`",
        "- `results/publication_tables/exact_validation_integrated_summary.csv`",
        "",
        "## Generated Figures",
        "",
        "- `results/publication_figures/exact_minimum_energy.png`",
        "- `results/publication_figures/exact_assignment_growth.png`",
        "- `results/publication_figures/exact_energy_decomposition.png`",
        "- `results/publication_figures/ising_coefficient_counts.png`",
        "",
        "## Summary",
        "",
        f"- Exact-validation sequences plotted: {len(exact_rows)}",
        f"- Energy audit rows plotted: {len(energy_rows)}",
        f"- QUBO-to-Ising coefficient rows read: {len(ising_rows)}",
        f"- Total exact-enumeration assignments checked: {total_assignments}",
        f"- Best exact minimum energy: {best_energy}",
        f"- Worst exact minimum energy: {worst_energy}",
        f"- Total Ising linear fields: {total_h_fields}",
        f"- Total Ising couplings: {total_j_couplings}",
        "",
        "## Figure Meanings",
        "",
        "### Exact Minimum Energy",
        "",
        "Shows the exact minimum QUBO energy found for each small RNA validation instance.",
        "",
        "### Assignment Growth",
        "",
        "Shows how exact enumeration grows with QUBO variable count. The y-axis uses a logarithmic scale because bitstring assignments grow exponentially.",
        "",
        "### Energy Decomposition",
        "",
        "Separates the exact optimum energy into linear reward, overlap penalty, crossing penalty, and interaction terms.",
        "",
        "### Ising Coefficient Counts",
        "",
        "Shows the number of constant, linear-field, and coupling terms produced by the QUBO-to-Ising conversion.",
        "",
        "## Safe Interpretation",
        "",
        "These figures support auditability and exact small-instance validation.",
        "",
        "They do not claim quantum advantage, final biological accuracy, or production-level RNA folding performance.",
    ]

    PHASE43_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_results_summary() -> None:
    content = """
# Phase 43 Update — Exact Validation Publication Figures

Phase 43 generated publication-ready figures from the exact-validation layer.

Generated figures:

- Exact minimum QUBO energy by RNA sequence
- Exact enumeration assignment growth
- QUBO energy decomposition
- QUBO-to-Ising coefficient counts

These figures strengthen the paper results section by turning the exact-validation CSV outputs into visual evidence.

Safe interpretation:

The figures show exact small-instance validation and auditability. They do not claim quantum advantage or final biological validation.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE43_MARKER, content)


def update_project_navigation() -> None:
    content = """
# Phase 43 — Exact Validation Publication Figures

Purpose:

Generate publication-ready figures from exact-validation outputs.

Main file:

`src/evaluation/phase43_exact_validation_figures.py`

Generated files:

`results/publication_figures/exact_minimum_energy.png`  
`results/publication_figures/exact_assignment_growth.png`  
`results/publication_figures/exact_energy_decomposition.png`  
`results/publication_figures/ising_coefficient_counts.png`  
`docs/phase43_exact_validation_figures.md`

Run:

`python src\\evaluation\\phase43_exact_validation_figures.py`

Safe interpretation:

Phase 43 visualizes exact small-instance validation. It supports auditability but does not claim quantum advantage or final biological accuracy.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE43_MARKER, content)


def main() -> None:
    exact_rows = read_csv(EXACT_RESULTS_TABLE)
    energy_rows = read_csv(ENERGY_AUDIT_SUMMARY_TABLE)
    ising_rows = read_csv(ISING_COEFFICIENTS_TABLE)
    integrated_rows = read_csv(INTEGRATED_SUMMARY_TABLE)

    if not exact_rows:
        raise FileNotFoundError(f"Missing or empty table: {EXACT_RESULTS_TABLE}")

    if not energy_rows:
        raise FileNotFoundError(f"Missing or empty table: {ENERGY_AUDIT_SUMMARY_TABLE}")

    if not ising_rows:
        raise FileNotFoundError(f"Missing or empty table: {ISING_COEFFICIENTS_TABLE}")

    plot_exact_minimum_energy(exact_rows)
    plot_assignment_growth(exact_rows)
    plot_energy_decomposition(energy_rows)
    plot_ising_coefficient_counts(ising_rows)

    write_phase43_doc(
        exact_rows=exact_rows,
        energy_rows=energy_rows,
        ising_rows=ising_rows,
    )

    update_results_summary()
    update_project_navigation()

    print("Phase 43 exact-validation publication figures complete.")
    print(f"Exact minimum energy figure: {EXACT_MIN_ENERGY_FIGURE}")
    print(f"Assignment growth figure: {ASSIGNMENT_GROWTH_FIGURE}")
    print(f"Energy decomposition figure: {ENERGY_DECOMPOSITION_FIGURE}")
    print(f"Ising coefficient counts figure: {ISING_COUNTS_FIGURE}")
    print(f"Phase 43 documentation: {PHASE43_DOC}")
    print(f"Integrated summary rows available: {len(integrated_rows)}")


if __name__ == "__main__":
    main()
