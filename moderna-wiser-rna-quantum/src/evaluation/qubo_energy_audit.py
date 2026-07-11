from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence


ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluation.exact_qubo_validator import (  # noqa: E402
    RNA_EXACT_DATASET,
    build_stem_qubo,
    clean_sequence,
    decoded_pairs,
    energy_decomposition,
    exact_enumeration,
    format_pair_labels,
    format_pairs_0_based,
    format_pairs_1_based,
    is_feasible,
    qubo_energy,
    selected_stems,
    stem_dot_bracket,
    bitstring_from_bits,
)


TABLE_DIR = ROOT / "results" / "publication_tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

AUDIT_PATH = TABLE_DIR / "qubo_energy_audit.csv"
SUMMARY_PATH = TABLE_DIR / "qubo_energy_audit_summary.csv"


def excel_safe_bitstring(bits: Sequence[int]) -> str:
    bitstring = bitstring_from_bits(bits)

    if bitstring and bitstring[0] in {"0", "1"}:
        return f"bits_{bitstring}"

    return bitstring


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


def selected_variable_names(bits: Sequence[int], qubo: Dict[str, Any]) -> str:
    return "; ".join(variable["name"] for variable in selected_stems(bits, qubo))


def context_fields(
    item: Dict[str, str],
    sequence: str,
    bits: Sequence[int],
    qubo: Dict[str, Any],
) -> Dict[str, Any]:
    pairs = sorted(decoded_pairs(bits, qubo))

    return {
        "sequence_id": item["sequence_id"],
        "sequence": sequence,
        "sequence_length": len(sequence),
        "variable_count": qubo["variable_count"],
        "quadratic_term_count": qubo["quadratic_term_count"],
        "qubo_density": qubo["qubo_density"],
        "best_bitstring": excel_safe_bitstring(bits),
        "selected_variables": selected_variable_names(bits, qubo),
        "decoded_pairs_0_based": format_pairs_0_based(pairs),
        "decoded_pairs_1_based": format_pairs_1_based(pairs),
        "decoded_pair_labels": format_pair_labels(sequence, pairs),
        "dot_bracket": stem_dot_bracket(len(sequence), set(pairs)),
        "feasible": is_feasible(bits, qubo),
    }


def make_summary_row(
    item: Dict[str, str],
    sequence: str,
    bits: Sequence[int],
    qubo: Dict[str, Any],
    exact: Dict[str, Any],
) -> Dict[str, Any]:
    decomposition = energy_decomposition(bits, qubo)

    return {
        **context_fields(item, sequence, bits, qubo),
        "exact_minimum_energy": exact["minimum_energy"],
        "degenerate_minimum_count": len(exact["degenerate_minima"]),
        "assignment_count": exact["assignment_count"],
        "linear_energy": decomposition["linear_energy"],
        "overlap_penalty_energy": decomposition["overlap_penalty_energy"],
        "crossing_penalty_energy": decomposition["crossing_penalty_energy"],
        "interaction_energy": decomposition["interaction_energy"],
        "total_energy": decomposition["total_energy"],
        "audit_status": "complete",
        "audit_note": "Exact optimum was audited term by term.",
    }


def make_linear_audit_rows(
    item: Dict[str, str],
    sequence: str,
    bits: Sequence[int],
    qubo: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    context = context_fields(item, sequence, bits, qubo)

    for variable in qubo["variables"]:
        index = variable["index"]
        active = bits[index] == 1
        coefficient = variable["linear_coefficient"]
        contribution = coefficient if active else 0.0

        rows.append(
            {
                **context,
                "audit_section": "linear_terms",
                "term_id": variable["name"],
                "term_type": "linear_stem_reward",
                "variable_i": variable["name"],
                "variable_j": "",
                "coefficient": coefficient,
                "active": active,
                "contribution": round(contribution, 9),
                "stem_length": variable["stem_length"],
                "stem_score": variable["stem_score"],
                "fragment_penalty": variable["fragment_penalty"],
                "local_context_penalty": variable["local_context_penalty"],
                "overlap_indicator": "",
                "crossing_indicator": "",
                "reason": "selected_stem_reward" if active else "inactive_stem",
                "assumption": variable["assumption"],
            }
        )

    return rows


def make_quadratic_audit_rows(
    item: Dict[str, str],
    sequence: str,
    bits: Sequence[int],
    qubo: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    context = context_fields(item, sequence, bits, qubo)

    for term in qubo["quadratic_terms"]:
        i = term["i"]
        j = term["j"]

        active = bits[i] == 1 and bits[j] == 1
        coefficient = term["coefficient"]
        contribution = coefficient if active else 0.0

        if term["overlap_indicator"] and term["crossing_indicator"]:
            term_type = "overlap_and_crossing_penalty"
        elif term["overlap_indicator"]:
            term_type = "overlap_penalty"
        elif term["crossing_indicator"]:
            term_type = "crossing_penalty"
        else:
            term_type = "compatible_interaction"

        rows.append(
            {
                **context,
                "audit_section": "quadratic_terms",
                "term_id": f"{term['var_i']}__{term['var_j']}",
                "term_type": term_type,
                "variable_i": term["var_i"],
                "variable_j": term["var_j"],
                "coefficient": coefficient,
                "active": active,
                "contribution": round(contribution, 9),
                "stem_length": "",
                "stem_score": "",
                "fragment_penalty": "",
                "local_context_penalty": "",
                "overlap_indicator": term["overlap_indicator"],
                "crossing_indicator": term["crossing_indicator"],
                "reason": term["reason"],
                "assumption": "Quadratic penalties discourage incompatible stem selections.",
            }
        )

    return rows


def make_total_check_rows(
    item: Dict[str, str],
    sequence: str,
    bits: Sequence[int],
    qubo: Dict[str, Any],
) -> List[Dict[str, Any]]:
    context = context_fields(item, sequence, bits, qubo)
    decomposition = energy_decomposition(bits, qubo)
    direct_energy = qubo_energy(bits, qubo)

    rows: List[Dict[str, Any]] = []

    total_components = [
        ("linear_energy_total", decomposition["linear_energy"], "Sum of active linear stem terms."),
        ("overlap_penalty_total", decomposition["overlap_penalty_energy"], "Sum of active overlap penalties."),
        ("crossing_penalty_total", decomposition["crossing_penalty_energy"], "Sum of active crossing penalties."),
        ("interaction_energy_total", decomposition["interaction_energy"], "Sum of active compatible interaction terms."),
        ("total_energy_check", decomposition["total_energy"], "Total from energy decomposition."),
        ("direct_qubo_energy_check", direct_energy, "Total from direct QUBO energy function."),
    ]

    for term_id, value, assumption in total_components:
        rows.append(
            {
                **context,
                "audit_section": "total_checks",
                "term_id": term_id,
                "term_type": "energy_total",
                "variable_i": "",
                "variable_j": "",
                "coefficient": "",
                "active": True,
                "contribution": value,
                "stem_length": "",
                "stem_score": "",
                "fragment_penalty": "",
                "local_context_penalty": "",
                "overlap_indicator": "",
                "crossing_indicator": "",
                "reason": term_id,
                "assumption": assumption,
            }
        )

    return rows


def make_skipped_row(
    item: Dict[str, str],
    sequence: str,
    qubo: Dict[str, Any],
    exact: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "sequence_id": item["sequence_id"],
        "sequence": sequence,
        "sequence_length": len(sequence),
        "variable_count": qubo["variable_count"],
        "quadratic_term_count": qubo["quadratic_term_count"],
        "qubo_density": qubo["qubo_density"],
        "best_bitstring": "",
        "selected_variables": "",
        "decoded_pairs_0_based": "",
        "decoded_pairs_1_based": "",
        "decoded_pair_labels": "",
        "dot_bracket": "",
        "feasible": "",
        "audit_section": "skipped",
        "term_id": "skipped",
        "term_type": "not_enumerated",
        "variable_i": "",
        "variable_j": "",
        "coefficient": "",
        "active": "",
        "contribution": "",
        "stem_length": "",
        "stem_score": "",
        "fragment_penalty": "",
        "local_context_penalty": "",
        "overlap_indicator": "",
        "crossing_indicator": "",
        "reason": "exact_enumeration_skipped",
        "assumption": exact["note"],
    }


def build_audit_tables() -> None:
    audit_rows: List[Dict[str, Any]] = []
    summary_rows: List[Dict[str, Any]] = []

    for item in RNA_EXACT_DATASET:
        sequence = clean_sequence(item["sequence"])
        qubo = build_stem_qubo(sequence)
        exact = exact_enumeration(qubo)

        if not exact["enumerated"]:
            audit_rows.append(make_skipped_row(item, sequence, qubo, exact))
            continue

        bits = tuple(int(value) for value in exact["best_bits"])

        summary_rows.append(make_summary_row(item, sequence, bits, qubo, exact))
        audit_rows.extend(make_linear_audit_rows(item, sequence, bits, qubo))
        audit_rows.extend(make_quadratic_audit_rows(item, sequence, bits, qubo))
        audit_rows.extend(make_total_check_rows(item, sequence, bits, qubo))

    write_csv(AUDIT_PATH, audit_rows)
    write_csv(SUMMARY_PATH, summary_rows)


def main() -> None:
    build_audit_tables()

    print("Phase 40 QUBO energy audit complete.")
    print(f"Energy audit table: {AUDIT_PATH}")
    print(f"Energy audit summary: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()