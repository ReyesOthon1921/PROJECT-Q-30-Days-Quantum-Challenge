from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]

TABLE_DIR = ROOT / "results" / "publication_tables"
DOCS_DIR = ROOT / "docs"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

FINAL_TABLE = TABLE_DIR / "final_publication_benchmark_table.csv"
FINAL_BACKUP_TABLE = TABLE_DIR / "final_publication_benchmark_table_pre_phase41_backup.csv"
INTEGRATED_TABLE = TABLE_DIR / "final_publication_benchmark_with_exact_validation.csv"
INTEGRATED_SUMMARY_TABLE = TABLE_DIR / "exact_validation_integrated_summary.csv"

EXACT_RESULTS_TABLE = TABLE_DIR / "exact_validation_results.csv"
ENERGY_AUDIT_SUMMARY_TABLE = TABLE_DIR / "qubo_energy_audit_summary.csv"
ISING_COEFFICIENTS_TABLE = TABLE_DIR / "qubo_to_ising_coefficients.csv"

PHASE41_DOC = DOCS_DIR / "phase41_exact_validation_integration.md"
RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"


PHASE41_MARKER = "<!-- PHASE41_EXACT_VALIDATION_INTEGRATION -->"


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


def normalize_sequence(value: str) -> str:
    value = str(value or "").upper().replace("T", "U")
    return "".join(base for base in value if base in {"A", "U", "G", "C"})


def normalize_header(value: str) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def get_value(row: Dict[str, Any], possible_names: List[str], default: str = "") -> str:
    normalized_lookup = {normalize_header(key): key for key in row.keys()}

    for name in possible_names:
        normalized_name = normalize_header(name)

        if normalized_name in normalized_lookup:
            return str(row.get(normalized_lookup[normalized_name], default))

    return default


def excel_safe_bitstring(value: str) -> str:
    value = str(value or "").strip()

    if value.startswith("bits_"):
        return value

    if value and all(character in {"0", "1"} for character in value):
        return f"bits_{value}"

    return value


def to_float(value: Any) -> Optional[float]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def to_int(value: Any) -> Optional[int]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except ValueError:
        return None


def build_exact_lookup(exact_rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}

    for row in exact_rows:
        sequence = normalize_sequence(get_value(row, ["sequence"]))
        sequence_id = get_value(row, ["sequence_id"])

        if sequence:
            lookup[f"sequence::{sequence}"] = row

        if sequence_id:
            lookup[f"sequence_id::{sequence_id}"] = row

    return lookup


def build_energy_lookup(energy_rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    lookup: Dict[str, Dict[str, str]] = {}

    for row in energy_rows:
        sequence_id = get_value(row, ["sequence_id"])
        sequence = normalize_sequence(get_value(row, ["sequence"]))

        if sequence_id:
            lookup[f"sequence_id::{sequence_id}"] = row

        if sequence:
            lookup[f"sequence::{sequence}"] = row

    return lookup


def build_ising_lookup(ising_rows: List[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    grouped_values: Dict[str, Dict[str, Any]] = {}

    for row in ising_rows:
        sequence_id = get_value(row, ["sequence_id"])

        if not sequence_id:
            continue

        group = grouped_values.setdefault(
            sequence_id,
            {
                "ising_constant_offset": "",
                "ising_linear_field_count": 0,
                "ising_coupling_count": 0,
                "ising_min_linear_field": "",
                "ising_max_linear_field": "",
                "ising_min_coupling": "",
                "ising_max_coupling": "",
                "h_values": [],
                "j_values": [],
            },
        )

        coefficient_type = get_value(row, ["coefficient_type"])
        value = to_float(get_value(row, ["value"]))

        if value is None:
            continue

        if coefficient_type == "constant_offset":
            group["ising_constant_offset"] = round(value, 9)

        elif coefficient_type == "linear_field":
            group["ising_linear_field_count"] += 1
            group["h_values"].append(value)

        elif coefficient_type == "coupling":
            group["ising_coupling_count"] += 1
            group["j_values"].append(value)

    final_lookup: Dict[str, Dict[str, Any]] = {}

    for sequence_id, group in grouped_values.items():
        h_values = group.pop("h_values")
        j_values = group.pop("j_values")

        if h_values:
            group["ising_min_linear_field"] = round(min(h_values), 9)
            group["ising_max_linear_field"] = round(max(h_values), 9)

        if j_values:
            group["ising_min_coupling"] = round(min(j_values), 9)
            group["ising_max_coupling"] = round(max(j_values), 9)

        final_lookup[sequence_id] = group

    return final_lookup


def find_exact_for_final_row(
    final_row: Dict[str, str],
    exact_lookup: Dict[str, Dict[str, str]],
) -> Optional[Dict[str, str]]:
    sequence = normalize_sequence(
        get_value(
            final_row,
            [
                "sequence",
                "rna_sequence",
                "Sequence",
                "RNA Sequence",
            ],
        )
    )

    sequence_id = get_value(
        final_row,
        [
            "sequence_id",
            "Sequence ID",
            "id",
            "sample_id",
        ],
    )

    if sequence_id and f"sequence_id::{sequence_id}" in exact_lookup:
        return exact_lookup[f"sequence_id::{sequence_id}"]

    if sequence and f"sequence::{sequence}" in exact_lookup:
        return exact_lookup[f"sequence::{sequence}"]

    return None


def get_energy_for_exact(
    exact_row: Dict[str, str],
    energy_lookup: Dict[str, Dict[str, str]],
) -> Dict[str, str]:
    sequence_id = get_value(exact_row, ["sequence_id"])
    sequence = normalize_sequence(get_value(exact_row, ["sequence"]))

    if sequence_id and f"sequence_id::{sequence_id}" in energy_lookup:
        return energy_lookup[f"sequence_id::{sequence_id}"]

    if sequence and f"sequence::{sequence}" in energy_lookup:
        return energy_lookup[f"sequence::{sequence}"]

    return {}


def phase41_exact_fields(
    exact_row: Optional[Dict[str, str]],
    energy_row: Optional[Dict[str, str]],
    ising_row: Optional[Dict[str, Any]],
    note: str,
) -> Dict[str, Any]:
    if exact_row is None:
        return {
            "phase41_exact_ground_truth_available": False,
            "phase41_exact_sequence_id": "",
            "phase41_exact_enumerated": "",
            "phase41_assignment_count": "",
            "phase41_exact_minimum_energy": "",
            "phase41_degenerate_minimum_count": "",
            "phase41_best_bitstring": "",
            "phase41_exact_feasible": "",
            "phase41_exact_dot_bracket": "",
            "phase41_exact_decoded_pairs_1_based": "",
            "phase41_linear_energy": "",
            "phase41_overlap_penalty_energy": "",
            "phase41_crossing_penalty_energy": "",
            "phase41_interaction_energy": "",
            "phase41_total_energy": "",
            "phase41_ising_constant_offset": "",
            "phase41_ising_linear_field_count": "",
            "phase41_ising_coupling_count": "",
            "phase41_ising_min_linear_field": "",
            "phase41_ising_max_linear_field": "",
            "phase41_ising_min_coupling": "",
            "phase41_ising_max_coupling": "",
            "phase41_validation_note": note,
        }

    energy_row = energy_row or {}
    ising_row = ising_row or {}

    return {
        "phase41_exact_ground_truth_available": True,
        "phase41_exact_sequence_id": get_value(exact_row, ["sequence_id"]),
        "phase41_exact_enumerated": get_value(exact_row, ["enumerated"]),
        "phase41_assignment_count": get_value(exact_row, ["assignment_count"]),
        "phase41_exact_minimum_energy": get_value(exact_row, ["exact_minimum_energy"]),
        "phase41_degenerate_minimum_count": get_value(exact_row, ["degenerate_minimum_count"]),
        "phase41_best_bitstring": excel_safe_bitstring(get_value(exact_row, ["best_bitstring"])),
        "phase41_exact_feasible": get_value(exact_row, ["feasible"]),
        "phase41_exact_dot_bracket": get_value(exact_row, ["dot_bracket"]),
        "phase41_exact_decoded_pairs_1_based": get_value(exact_row, ["decoded_pairs_1_based"]),
        "phase41_linear_energy": get_value(energy_row, ["linear_energy"], get_value(exact_row, ["linear_energy"])),
        "phase41_overlap_penalty_energy": get_value(energy_row, ["overlap_penalty_energy"], get_value(exact_row, ["overlap_penalty_energy"])),
        "phase41_crossing_penalty_energy": get_value(energy_row, ["crossing_penalty_energy"], get_value(exact_row, ["crossing_penalty_energy"])),
        "phase41_interaction_energy": get_value(energy_row, ["interaction_energy"], get_value(exact_row, ["interaction_energy"])),
        "phase41_total_energy": get_value(energy_row, ["total_energy"], get_value(exact_row, ["total_energy"])),
        "phase41_ising_constant_offset": ising_row.get("ising_constant_offset", ""),
        "phase41_ising_linear_field_count": ising_row.get("ising_linear_field_count", ""),
        "phase41_ising_coupling_count": ising_row.get("ising_coupling_count", ""),
        "phase41_ising_min_linear_field": ising_row.get("ising_min_linear_field", ""),
        "phase41_ising_max_linear_field": ising_row.get("ising_max_linear_field", ""),
        "phase41_ising_min_coupling": ising_row.get("ising_min_coupling", ""),
        "phase41_ising_max_coupling": ising_row.get("ising_max_coupling", ""),
        "phase41_validation_note": note,
    }


def make_integrated_rows(
    final_rows: List[Dict[str, str]],
    exact_rows: List[Dict[str, str]],
    exact_lookup: Dict[str, Dict[str, str]],
    energy_lookup: Dict[str, Dict[str, str]],
    ising_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    integrated_rows: List[Dict[str, Any]] = []

    for final_row in final_rows:
        exact_row = find_exact_for_final_row(final_row, exact_lookup)

        if exact_row is None:
            exact_fields = phase41_exact_fields(
                exact_row=None,
                energy_row=None,
                ising_row=None,
                note="No exact-validation match for this benchmark row. Exact-control rows are included separately.",
            )
        else:
            energy_row = get_energy_for_exact(exact_row, energy_lookup)
            sequence_id = get_value(exact_row, ["sequence_id"])
            ising_row = ising_lookup.get(sequence_id, {})

            exact_fields = phase41_exact_fields(
                exact_row=exact_row,
                energy_row=energy_row,
                ising_row=ising_row,
                note="Exact validation matched this benchmark row.",
            )

        integrated_rows.append(
            {
                **final_row,
                "phase41_row_type": "original_benchmark_row",
                **exact_fields,
            }
        )

    for exact_row in exact_rows:
        sequence_id = get_value(exact_row, ["sequence_id"])
        sequence = get_value(exact_row, ["sequence"])
        energy_row = get_energy_for_exact(exact_row, energy_lookup)
        ising_row = ising_lookup.get(sequence_id, {})

        exact_fields = phase41_exact_fields(
            exact_row=exact_row,
            energy_row=energy_row,
            ising_row=ising_row,
            note="Phase 41 exact-validation control row added to final benchmark.",
        )

        integrated_rows.append(
            {
                "sequence_id": sequence_id,
                "sequence": sequence,
                "length": get_value(exact_row, ["length"]),
                "variable_count": get_value(exact_row, ["variable_count"]),
                "quadratic_term_count": get_value(exact_row, ["quadratic_term_count"]),
                "qubo_density": get_value(exact_row, ["qubo_density"]),
                "classical_energy": "",
                "quantum_energy": "",
                "direct_qubits": get_value(exact_row, ["variable_count"]),
                "compressed_qubits": "",
                "runtime": "",
                "f1_score": "",
                "notes": "Exact small-instance validation control row.",
                "phase41_row_type": "exact_validation_control_row",
                **exact_fields,
            }
        )

    return integrated_rows


def make_integrated_summary_rows(
    exact_rows: List[Dict[str, str]],
    energy_lookup: Dict[str, Dict[str, str]],
    ising_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for exact_row in exact_rows:
        sequence_id = get_value(exact_row, ["sequence_id"])
        energy_row = get_energy_for_exact(exact_row, energy_lookup)
        ising_row = ising_lookup.get(sequence_id, {})

        row = {
            "sequence_id": sequence_id,
            "sequence": get_value(exact_row, ["sequence"]),
            "length": get_value(exact_row, ["length"]),
            "variable_count": get_value(exact_row, ["variable_count"]),
            "assignment_count": get_value(exact_row, ["assignment_count"]),
            "exact_minimum_energy": get_value(exact_row, ["exact_minimum_energy"]),
            "degenerate_minimum_count": get_value(exact_row, ["degenerate_minimum_count"]),
            "best_bitstring": excel_safe_bitstring(get_value(exact_row, ["best_bitstring"])),
            "feasible": get_value(exact_row, ["feasible"]),
            "dot_bracket": get_value(exact_row, ["dot_bracket"]),
            "linear_energy": get_value(energy_row, ["linear_energy"], get_value(exact_row, ["linear_energy"])),
            "overlap_penalty_energy": get_value(energy_row, ["overlap_penalty_energy"], get_value(exact_row, ["overlap_penalty_energy"])),
            "crossing_penalty_energy": get_value(energy_row, ["crossing_penalty_energy"], get_value(exact_row, ["crossing_penalty_energy"])),
            "interaction_energy": get_value(energy_row, ["interaction_energy"], get_value(exact_row, ["interaction_energy"])),
            "total_energy": get_value(energy_row, ["total_energy"], get_value(exact_row, ["total_energy"])),
            "ising_constant_offset": ising_row.get("ising_constant_offset", ""),
            "ising_linear_field_count": ising_row.get("ising_linear_field_count", ""),
            "ising_coupling_count": ising_row.get("ising_coupling_count", ""),
            "integration_note": "Exact optimum and audit summary integrated into Phase 41 benchmark layer.",
        }

        rows.append(row)

    return rows


def write_phase41_doc(
    final_row_count: int,
    exact_row_count: int,
    integrated_row_count: int,
) -> None:
    lines = [
        "# Phase 41 — Exact Validation Integration Into Final Benchmark",
        "",
        "## Purpose",
        "",
        "Phase 41 integrates the exact-validation layer back into the final publication benchmark.",
        "",
        "The final benchmark now connects the earlier publication benchmark outputs with exact small-instance ground truth.",
        "",
        "## Inputs",
        "",
        "- `results/publication_tables/final_publication_benchmark_table.csv`",
        "- `results/publication_tables/exact_validation_results.csv`",
        "- `results/publication_tables/qubo_energy_audit_summary.csv`",
        "- `results/publication_tables/qubo_to_ising_coefficients.csv`",
        "",
        "## Outputs",
        "",
        "- `results/publication_tables/final_publication_benchmark_table.csv`",
        "- `results/publication_tables/final_publication_benchmark_table_pre_phase41_backup.csv`",
        "- `results/publication_tables/final_publication_benchmark_with_exact_validation.csv`",
        "- `results/publication_tables/exact_validation_integrated_summary.csv`",
        "- `docs/phase41_exact_validation_integration.md`",
        "",
        "## What Changed",
        "",
        "The final publication benchmark now includes Phase 41 columns for:",
        "",
        "- exact ground-truth availability,",
        "- exact sequence ID,",
        "- assignment count,",
        "- exact minimum energy,",
        "- degenerate minimum count,",
        "- best bitstring,",
        "- feasibility,",
        "- decoded dot-bracket structure,",
        "- decoded base pairs,",
        "- linear energy,",
        "- overlap penalty energy,",
        "- crossing penalty energy,",
        "- total QUBO energy,",
        "- QUBO-to-Ising constant offset,",
        "- Ising linear-field count,",
        "- Ising coupling count,",
        "- Ising coefficient ranges.",
        "",
        "## Row Counts",
        "",
        f"- Original benchmark rows loaded: {final_row_count}",
        f"- Exact-validation rows loaded: {exact_row_count}",
        f"- Integrated benchmark rows written: {integrated_row_count}",
        "",
        "## Research Meaning",
        "",
        "This phase strengthens the research paper because the benchmark no longer only reports classical, quantum, and compression outputs.",
        "",
        "It now also includes exact small-instance ground truth.",
        "",
        "This helps separate QUBO validity from biological accuracy and gives a stronger foundation before interpreting QAOA, VQE, hardware-readiness, or QRAO compression layers.",
        "",
        "## Safe Claim",
        "",
        "This is still a prototype benchmark and feasibility framework.",
        "",
        "The project does not claim quantum advantage, clinical accuracy, final biological validation, or proven compression improvement.",
        "",
        "The contribution is the integrated and auditable bioinformatics-to-quantum benchmark workflow.",
    ]

    PHASE41_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_once(path: Path, marker: str, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = ""

    if marker in existing:
        return

    updated = existing.rstrip() + "\n\n" + marker + "\n" + content.strip() + "\n"
    path.write_text(updated, encoding="utf-8")


def update_results_summary_doc() -> None:
    content = """
# Phase 41 Update — Exact Validation Integration

Phase 41 integrated the exact-validation outputs into the final benchmark layer.

The final publication benchmark now includes exact small-instance ground truth, including exact minimum energy, assignment count, feasibility, best bitstring, energy audit terms, and QUBO-to-Ising coefficient summaries.

This strengthens the results section because the benchmark now connects:

RNA/QUBO formulation  
→ exact small-instance validation  
→ energy audit  
→ QUBO-to-Ising mapping  
→ classical/quantum/compression benchmark context.

Important interpretation:

This does not prove quantum advantage. It makes the benchmark more auditable and gives a stronger validation foundation before interpreting QAOA, VQE, hardware-readiness, or QRAO compression outputs.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE41_MARKER, content)


def update_project_navigation_doc() -> None:
    content = """
# Phase 41 — Exact Validation Integration Into Final Benchmark

Purpose:

Merge exact optimum, feasibility, exact-validation notes, QUBO-to-Ising data, and energy audit summaries back into the final publication benchmark table and results summary.

Main file:

`src/evaluation/phase41_exact_validation_benchmark_integration.py`

Generated or updated files:

`results/publication_tables/final_publication_benchmark_table.csv`  
`results/publication_tables/final_publication_benchmark_table_pre_phase41_backup.csv`  
`results/publication_tables/final_publication_benchmark_with_exact_validation.csv`  
`results/publication_tables/exact_validation_integrated_summary.csv`  
`docs/phase41_exact_validation_integration.md`  
`docs/results_summary.md`  
`docs/project_navigation_guide.md`

Run:

`python src\\evaluation\\phase41_exact_validation_benchmark_integration.py`

Safe interpretation:

Phase 41 adds exact small-instance ground truth to the final benchmark. It supports auditability and validation, but it does not claim quantum advantage or final biological accuracy.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE41_MARKER, content)


def main() -> None:
    final_rows = read_csv(FINAL_TABLE)
    exact_rows = read_csv(EXACT_RESULTS_TABLE)
    energy_rows = read_csv(ENERGY_AUDIT_SUMMARY_TABLE)
    ising_rows = read_csv(ISING_COEFFICIENTS_TABLE)

    if not exact_rows:
        raise FileNotFoundError(
            f"No exact-validation rows found. Expected file: {EXACT_RESULTS_TABLE}"
        )

    if final_rows and not FINAL_BACKUP_TABLE.exists():
        write_csv(FINAL_BACKUP_TABLE, final_rows)

    exact_lookup = build_exact_lookup(exact_rows)
    energy_lookup = build_energy_lookup(energy_rows)
    ising_lookup = build_ising_lookup(ising_rows)

    integrated_rows = make_integrated_rows(
        final_rows=final_rows,
        exact_rows=exact_rows,
        exact_lookup=exact_lookup,
        energy_lookup=energy_lookup,
        ising_lookup=ising_lookup,
    )

    summary_rows = make_integrated_summary_rows(
        exact_rows=exact_rows,
        energy_lookup=energy_lookup,
        ising_lookup=ising_lookup,
    )

    write_csv(FINAL_TABLE, integrated_rows)
    write_csv(INTEGRATED_TABLE, integrated_rows)
    write_csv(INTEGRATED_SUMMARY_TABLE, summary_rows)

    write_phase41_doc(
        final_row_count=len(final_rows),
        exact_row_count=len(exact_rows),
        integrated_row_count=len(integrated_rows),
    )

    update_results_summary_doc()
    update_project_navigation_doc()

    print("Phase 41 exact-validation benchmark integration complete.")
    print(f"Updated final benchmark table: {FINAL_TABLE}")
    print(f"Backup of previous final benchmark: {FINAL_BACKUP_TABLE}")
    print(f"Integrated benchmark copy: {INTEGRATED_TABLE}")
    print(f"Exact validation summary: {INTEGRATED_SUMMARY_TABLE}")
    print(f"Phase 41 documentation: {PHASE41_DOC}")
    print(f"Updated results summary: {RESULTS_SUMMARY_DOC}")
    print(f"Updated project navigation guide: {PROJECT_NAVIGATION_DOC}")


if __name__ == "__main__":
    main()