from __future__ import annotations

import csv
import itertools
import math
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "publication_tables"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

TRACEABILITY_PATH = TABLE_DIR / "stem_traceability_table.csv"
EXACT_RESULTS_PATH = TABLE_DIR / "exact_validation_results.csv"
EXACT_MINIMA_PATH = TABLE_DIR / "exact_validation_minima.csv"
ISING_PATH = TABLE_DIR / "qubo_to_ising_coefficients.csv"

MIN_LOOP = 3
MAX_STEMS_FOR_EXACT = 16
OVERLAP_PENALTY = 8.0
CROSSING_PENALTY = 6.0
GAMMA_INTERACTION = 0.0

PAIR_RULES = {
    ("A", "U"),
    ("U", "A"),
    ("G", "C"),
    ("C", "G"),
    ("G", "U"),
    ("U", "G"),
}

RNA_EXACT_DATASET = [
    {
        "sequence_id": "EXACT_01_short_hairpin",
        "sequence": "GGGAAAUCC",
        "source": "phase40_control",
        "note": "Small controlled exact-enumeration instance.",
    },
    {
        "sequence_id": "EXACT_02_balanced_short",
        "sequence": "AUGCUAGCUA",
        "source": "phase40_control",
        "note": "Balanced short RNA instance for QUBO audit.",
    },
    {
        "sequence_id": "EXACT_03_gc_rich",
        "sequence": "GCGCGAUUCGC",
        "source": "phase40_control",
        "note": "GC-rich small instance for conflict and coefficient checking.",
    },
    {
        "sequence_id": "EXACT_04_demo_subset",
        "sequence": "GGCGCAAAACUUGUCGAAU",
        "source": "phase40_demo_subset",
        "note": "Truncated demo-style sequence kept small for exact validation.",
    },
]


Pair = Tuple[int, int]
Stem = Tuple[Pair, ...]


def clean_sequence(sequence: str) -> str:
    sequence = sequence.upper().replace("T", "U")
    return "".join(base for base in sequence if base in {"A", "U", "G", "C"})


def can_pair(left: str, right: str) -> bool:
    return (left, right) in PAIR_RULES


def pair_label(sequence: str, pair: Pair) -> str:
    i, j = pair
    return f"{sequence[i]}{i + 1}-{sequence[j]}{j + 1}"


def candidate_pairs(sequence: str, min_loop: int = MIN_LOOP) -> List[Pair]:
    pairs: List[Pair] = []

    for i in range(len(sequence)):
        for j in range(i + min_loop + 1, len(sequence)):
            if can_pair(sequence[i], sequence[j]):
                pairs.append((i, j))

    return pairs


def pair_score(sequence: str, pair: Pair) -> float:
    i, j = pair
    bases = (sequence[i], sequence[j])

    if bases in {("G", "C"), ("C", "G")}:
        return 3.0

    if bases in {("A", "U"), ("U", "A")}:
        return 2.0

    if bases in {("G", "U"), ("U", "G")}:
        return 1.0

    return 0.0


def stem_score(sequence: str, stem: Stem) -> float:
    return sum(pair_score(sequence, pair) for pair in stem)


def candidate_stems(
    sequence: str,
    min_stem_length: int = 1,
    max_stem_length: int = 3,
) -> List[Stem]:
    pair_set = set(candidate_pairs(sequence))
    stems: Set[Stem] = set()

    for i, j in sorted(pair_set):
        current: List[Pair] = []

        for offset in range(max_stem_length):
            left = i + offset
            right = j - offset

            if left >= right:
                break

            if (left, right) not in pair_set:
                break

            current.append((left, right))

        if len(current) >= min_stem_length:
            stems.add(tuple(current))

    sorted_stems = sorted(
        stems,
        key=lambda item: (stem_score(sequence, item), len(item), item[0][1] - item[0][0]),
        reverse=True,
    )

    return sorted_stems[:MAX_STEMS_FOR_EXACT]


def bases_used(stem: Stem) -> Set[int]:
    return {base for pair in stem for base in pair}


def has_overlap(stem_a: Stem, stem_b: Stem) -> bool:
    return bool(bases_used(stem_a).intersection(bases_used(stem_b)))


def pair_crosses(pair_a: Pair, pair_b: Pair) -> bool:
    i, j = pair_a
    k, l = pair_b

    return (i < k < j < l) or (k < i < l < j)


def has_crossing(stem_a: Stem, stem_b: Stem) -> bool:
    for pair_a in stem_a:
        for pair_b in stem_b:
            if pair_crosses(pair_a, pair_b):
                return True

    return False


def stem_dot_bracket(length: int, pairs: Set[Pair]) -> str:
    chars = ["." for _ in range(length)]

    for i, j in sorted(pairs):
        if chars[i] == "." and chars[j] == ".":
            chars[i] = "("
            chars[j] = ")"

    return "".join(chars)


def format_pairs_0_based(pairs: Sequence[Pair]) -> str:
    return "; ".join(f"({i},{j})" for i, j in pairs)


def format_pairs_1_based(pairs: Sequence[Pair]) -> str:
    return "; ".join(f"({i + 1},{j + 1})" for i, j in pairs)


def format_pair_labels(sequence: str, pairs: Sequence[Pair]) -> str:
    return "; ".join(pair_label(sequence, pair) for pair in pairs)


def build_stem_qubo(sequence: str) -> Dict[str, Any]:
    stems = candidate_stems(sequence)

    variables: List[Dict[str, Any]] = []

    for index, stem in enumerate(stems):
        score = stem_score(sequence, stem)
        fragment_penalty = 0.0 if len(stem) >= 2 else 0.25
        local_context_penalty = 0.0
        linear_coefficient = -score + fragment_penalty + local_context_penalty

        variables.append(
            {
                "index": index,
                "name": f"x_{index}",
                "stem": stem,
                "stem_length": len(stem),
                "stem_score": round(score, 6),
                "fragment_penalty": round(fragment_penalty, 6),
                "local_context_penalty": round(local_context_penalty, 6),
                "linear_coefficient": round(linear_coefficient, 6),
                "assumption": "Favorable stems receive negative linear energy; single-pair stems receive a small fragment penalty.",
            }
        )

    quadratic_terms: List[Dict[str, Any]] = []

    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            overlap = has_overlap(stems[i], stems[j])
            crossing = has_crossing(stems[i], stems[j])

            overlap_value = 1 if overlap else 0
            crossing_value = 1 if crossing else 0

            coefficient = (
                OVERLAP_PENALTY * overlap_value
                + CROSSING_PENALTY * crossing_value
                + GAMMA_INTERACTION
            )

            if coefficient != 0:
                if overlap and crossing:
                    reason = "overlap_and_forbidden_crossing"
                elif overlap:
                    reason = "overlap_conflict"
                elif crossing:
                    reason = "forbidden_crossing_conflict"
                else:
                    reason = "compatible_interaction"

                quadratic_terms.append(
                    {
                        "i": i,
                        "j": j,
                        "var_i": f"x_{i}",
                        "var_j": f"x_{j}",
                        "overlap_indicator": overlap_value,
                        "crossing_indicator": crossing_value,
                        "gamma_interaction": GAMMA_INTERACTION,
                        "coefficient": round(coefficient, 6),
                        "reason": reason,
                    }
                )

    possible_quadratic = max(1, len(stems) * (len(stems) - 1) / 2)
    density = len(quadratic_terms) / possible_quadratic

    return {
        "sequence": sequence,
        "variables": variables,
        "quadratic_terms": quadratic_terms,
        "variable_count": len(variables),
        "quadratic_term_count": len(quadratic_terms),
        "qubo_density": round(density, 6),
    }


def qubo_energy(bits: Sequence[int], qubo: Dict[str, Any]) -> float:
    energy = 0.0

    for variable in qubo["variables"]:
        index = variable["index"]

        if bits[index] == 1:
            energy += variable["linear_coefficient"]

    for term in qubo["quadratic_terms"]:
        i = term["i"]
        j = term["j"]

        if bits[i] == 1 and bits[j] == 1:
            energy += term["coefficient"]

    return round(energy, 9)


def energy_decomposition(bits: Sequence[int], qubo: Dict[str, Any]) -> Dict[str, float]:
    linear = 0.0
    overlap = 0.0
    crossing = 0.0
    interaction = 0.0

    for variable in qubo["variables"]:
        index = variable["index"]

        if bits[index] == 1:
            linear += variable["linear_coefficient"]

    for term in qubo["quadratic_terms"]:
        i = term["i"]
        j = term["j"]

        if bits[i] == 1 and bits[j] == 1:
            if term["overlap_indicator"]:
                overlap += OVERLAP_PENALTY

            if term["crossing_indicator"]:
                crossing += CROSSING_PENALTY

            interaction += term["gamma_interaction"]

    total = linear + overlap + crossing + interaction

    return {
        "linear_energy": round(linear, 9),
        "overlap_penalty_energy": round(overlap, 9),
        "crossing_penalty_energy": round(crossing, 9),
        "interaction_energy": round(interaction, 9),
        "total_energy": round(total, 9),
    }


def selected_stems(bits: Sequence[int], qubo: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        variable
        for variable in qubo["variables"]
        if bits[variable["index"]] == 1
    ]


def decoded_pairs(bits: Sequence[int], qubo: Dict[str, Any]) -> Set[Pair]:
    pairs: Set[Pair] = set()

    for variable in selected_stems(bits, qubo):
        for pair in variable["stem"]:
            pairs.add(pair)

    return pairs


def is_feasible(bits: Sequence[int], qubo: Dict[str, Any]) -> bool:
    for term in qubo["quadratic_terms"]:
        i = term["i"]
        j = term["j"]

        if bits[i] == 1 and bits[j] == 1:
            if term["overlap_indicator"] or term["crossing_indicator"]:
                return False

    return True


def bitstring_from_bits(bits: Sequence[int]) -> str:
    return "".join(str(bit) for bit in bits)


def exact_enumeration(qubo: Dict[str, Any]) -> Dict[str, Any]:
    variable_count = qubo["variable_count"]

    if variable_count > MAX_STEMS_FOR_EXACT:
        return {
            "enumerated": False,
            "assignment_count": 0,
            "minimum_energy": None,
            "best_bits": [],
            "degenerate_minima": [],
            "note": f"Skipped because variable count {variable_count} exceeds exact limit {MAX_STEMS_FOR_EXACT}.",
        }

    minimum_energy = math.inf
    degenerate_minima: List[Tuple[int, ...]] = []
    assignment_count = 0
    tolerance = 1e-9

    for bits in itertools.product([0, 1], repeat=variable_count):
        assignment_count += 1
        energy = qubo_energy(bits, qubo)

        if energy < minimum_energy - tolerance:
            minimum_energy = energy
            degenerate_minima = [bits]
        elif abs(energy - minimum_energy) <= tolerance:
            degenerate_minima.append(bits)

    best_bits = list(degenerate_minima[0]) if degenerate_minima else []

    return {
        "enumerated": True,
        "assignment_count": assignment_count,
        "minimum_energy": round(minimum_energy, 9),
        "best_bits": best_bits,
        "degenerate_minima": degenerate_minima,
        "note": "Exact enumeration completed for all bitstrings.",
    }


def make_traceability_rows(
    sequence_id: str,
    sequence: str,
    qubo: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for variable in qubo["variables"]:
        index = variable["index"]
        stem = variable["stem"]

        connected_terms = [
            term
            for term in qubo["quadratic_terms"]
            if term["i"] == index or term["j"] == index
        ]

        overlap_count = sum(1 for term in connected_terms if term["overlap_indicator"])
        crossing_count = sum(1 for term in connected_terms if term["crossing_indicator"])

        connected_variables = []

        for term in connected_terms:
            other_index = term["j"] if term["i"] == index else term["i"]
            connected_variables.append(f"x_{other_index}:{term['reason']}:{term['coefficient']}")

        rows.append(
            {
                "sequence_id": sequence_id,
                "sequence": sequence,
                "variable": variable["name"],
                "variable_index": index,
                "stem_length": variable["stem_length"],
                "stem_score": variable["stem_score"],
                "fragment_penalty": variable["fragment_penalty"],
                "local_context_penalty": variable["local_context_penalty"],
                "linear_coefficient": variable["linear_coefficient"],
                "stem_pairs_0_based": format_pairs_0_based(stem),
                "stem_pairs_1_based": format_pairs_1_based(stem),
                "stem_pair_labels": format_pair_labels(sequence, stem),
                "overlap_conflict_count": overlap_count,
                "crossing_conflict_count": crossing_count,
                "total_conflict_count": len(connected_terms),
                "connected_variables": " | ".join(connected_variables),
                "assumption": variable["assumption"],
            }
        )

    return rows


def make_exact_result_row(
    item: Dict[str, str],
    sequence: str,
    qubo: Dict[str, Any],
    exact: Dict[str, Any],
) -> Dict[str, Any]:
    if not exact["enumerated"]:
        return {
            "sequence_id": item["sequence_id"],
            "sequence": sequence,
            "length": len(sequence),
            "variable_count": qubo["variable_count"],
            "quadratic_term_count": qubo["quadratic_term_count"],
            "qubo_density": qubo["qubo_density"],
            "enumerated": False,
            "assignment_count": exact["assignment_count"],
            "exact_minimum_energy": "",
            "degenerate_minimum_count": "",
            "best_bitstring": "",
            "selected_variables": "",
            "decoded_pairs_0_based": "",
            "decoded_pairs_1_based": "",
            "dot_bracket": "",
            "feasible": "",
            "linear_energy": "",
            "overlap_penalty_energy": "",
            "crossing_penalty_energy": "",
            "interaction_energy": "",
            "total_energy": "",
            "note": exact["note"],
        }

    best_bits = exact["best_bits"]
    selected = selected_stems(best_bits, qubo)
    pairs = sorted(decoded_pairs(best_bits, qubo))
    dot_bracket = stem_dot_bracket(len(sequence), set(pairs))
    decomposition = energy_decomposition(best_bits, qubo)

    return {
        "sequence_id": item["sequence_id"],
        "sequence": sequence,
        "length": len(sequence),
        "variable_count": qubo["variable_count"],
        "quadratic_term_count": qubo["quadratic_term_count"],
        "qubo_density": qubo["qubo_density"],
        "enumerated": True,
        "assignment_count": exact["assignment_count"],
        "exact_minimum_energy": exact["minimum_energy"],
        "degenerate_minimum_count": len(exact["degenerate_minima"]),
        "best_bitstring": bitstring_from_bits(best_bits),
        "selected_variables": "; ".join(variable["name"] for variable in selected),
        "decoded_pairs_0_based": format_pairs_0_based(pairs),
        "decoded_pairs_1_based": format_pairs_1_based(pairs),
        "dot_bracket": dot_bracket,
        "feasible": is_feasible(best_bits, qubo),
        "linear_energy": decomposition["linear_energy"],
        "overlap_penalty_energy": decomposition["overlap_penalty_energy"],
        "crossing_penalty_energy": decomposition["crossing_penalty_energy"],
        "interaction_energy": decomposition["interaction_energy"],
        "total_energy": decomposition["total_energy"],
        "note": exact["note"],
    }


def make_minima_rows(
    sequence_id: str,
    sequence: str,
    qubo: Dict[str, Any],
    exact: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    if not exact["enumerated"]:
        return rows

    for rank, bits in enumerate(exact["degenerate_minima"][:25], start=1):
        pairs = sorted(decoded_pairs(bits, qubo))
        selected = selected_stems(bits, qubo)

        rows.append(
            {
                "sequence_id": sequence_id,
                "minimum_rank": rank,
                "bitstring": bitstring_from_bits(bits),
                "energy": qubo_energy(bits, qubo),
                "feasible": is_feasible(bits, qubo),
                "selected_variables": "; ".join(variable["name"] for variable in selected),
                "decoded_pairs_0_based": format_pairs_0_based(pairs),
                "decoded_pairs_1_based": format_pairs_1_based(pairs),
                "decoded_pair_labels": format_pair_labels(sequence, pairs),
                "dot_bracket": stem_dot_bracket(len(sequence), set(pairs)),
            }
        )

    return rows


def make_ising_rows(
    sequence_id: str,
    qubo: Dict[str, Any],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    linear_sum = sum(variable["linear_coefficient"] for variable in qubo["variables"])
    quadratic_sum = sum(term["coefficient"] for term in qubo["quadratic_terms"])
    constant_offset = 0.5 * linear_sum + 0.25 * quadratic_sum

    rows.append(
        {
            "sequence_id": sequence_id,
            "coefficient_type": "constant_offset",
            "term": "C",
            "value": round(constant_offset, 9),
            "mapping_note": "C shifts energy but does not change the minimizing bitstring.",
        }
    )

    for variable in qubo["variables"]:
        index = variable["index"]
        a_i = variable["linear_coefficient"]

        connected_b_sum = 0.0

        for term in qubo["quadratic_terms"]:
            if term["i"] == index or term["j"] == index:
                connected_b_sum += term["coefficient"]

        h_i = -0.5 * a_i - 0.25 * connected_b_sum

        rows.append(
            {
                "sequence_id": sequence_id,
                "coefficient_type": "linear_field",
                "term": f"h_{index}",
                "value": round(h_i, 9),
                "mapping_note": "h_i = -a_i/2 - one fourth of connected quadratic coefficients.",
            }
        )

    for term in qubo["quadratic_terms"]:
        j_ij = term["coefficient"] / 4.0

        rows.append(
            {
                "sequence_id": sequence_id,
                "coefficient_type": "coupling",
                "term": f"J_{term['i']}_{term['j']}",
                "value": round(j_ij, 9),
                "mapping_note": "J_ij = b_ij / 4.",
            }
        )

    return rows


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


def main() -> None:
    traceability_rows: List[Dict[str, Any]] = []
    exact_result_rows: List[Dict[str, Any]] = []
    exact_minima_rows: List[Dict[str, Any]] = []
    ising_rows: List[Dict[str, Any]] = []

    for item in RNA_EXACT_DATASET:
        sequence_id = item["sequence_id"]
        sequence = clean_sequence(item["sequence"])
        qubo = build_stem_qubo(sequence)
        exact = exact_enumeration(qubo)

        traceability_rows.extend(make_traceability_rows(sequence_id, sequence, qubo))
        exact_result_rows.append(make_exact_result_row(item, sequence, qubo, exact))
        exact_minima_rows.extend(make_minima_rows(sequence_id, sequence, qubo, exact))
        ising_rows.extend(make_ising_rows(sequence_id, qubo))

    write_csv(TRACEABILITY_PATH, traceability_rows)
    write_csv(EXACT_RESULTS_PATH, exact_result_rows)
    write_csv(EXACT_MINIMA_PATH, exact_minima_rows)
    write_csv(ISING_PATH, ising_rows)

    print("Phase 40 exact QUBO validation complete.")
    print(f"Traceability table: {TRACEABILITY_PATH}")
    print(f"Exact validation results: {EXACT_RESULTS_PATH}")
    print(f"Exact minima table: {EXACT_MINIMA_PATH}")
    print(f"QUBO-to-Ising coefficients: {ISING_PATH}")


if __name__ == "__main__":
    main()