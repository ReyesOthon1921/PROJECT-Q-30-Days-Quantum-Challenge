"""
candidate_pairs.py

Phase 5 QUBO preparation.

This module turns valid RNA base-pair candidates into optimization variables.

Example:
    x_0 = 1 means candidate pair 0 is selected.
    x_0 = 0 means candidate pair 0 is not selected.
"""

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence, PAIR_TYPES


def generate_candidate_pairs(
    sequence: str,
    min_loop_length: int = 3,
    allow_wobble: bool = True,
) -> list:
    """
    Generate QUBO-ready candidate base-pair variables.

    Uses 0-based indexing.
    """
    cleaned = clean_sequence(sequence)

    if not validate_rna_sequence(cleaned):
        raise ValueError("Invalid RNA sequence. Use only A, U, G, and C.")

    candidates = []
    variable_index = 0

    for i in range(len(cleaned)):
        for j in range(i + min_loop_length + 1, len(cleaned)):
            pair = (cleaned[i], cleaned[j])

            if pair not in PAIR_TYPES:
                continue

            pair_type = PAIR_TYPES[pair]

            if "wobble" in pair_type and not allow_wobble:
                continue

            candidates.append(
                {
                    "variable_index": variable_index,
                    "variable_name": f"x_{variable_index}",
                    "i": i,
                    "j": j,
                    "left_base": cleaned[i],
                    "right_base": cleaned[j],
                    "pair_type": pair_type,
                    "distance": j - i,
                }
            )

            variable_index += 1

    return candidates


def build_pair_index_map(candidates: list) -> dict:
    """
    Map each base-pair position to a QUBO variable name.
    """
    pair_index_map = {}

    for candidate in candidates:
        pair = (candidate["i"], candidate["j"])
        pair_index_map[pair] = candidate["variable_name"]

    return pair_index_map


def summarize_candidate_pairs(sequence: str) -> dict:
    """
    Return a summary of candidate base-pair variables.
    """
    cleaned = clean_sequence(sequence)
    candidates = generate_candidate_pairs(cleaned)
    pair_index_map = build_pair_index_map(candidates)

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "candidate_pair_count": len(candidates),
        "estimated_binary_variables": len(candidates),
        "estimated_qubits": len(candidates),
        "first_10_candidate_pairs": candidates[:10],
        "first_10_pair_index_map": list(pair_index_map.items())[:10],
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    summary = summarize_candidate_pairs(sequence)

    print("Candidate pair summary")
    print("----------------------")
    for key, value in summary.items():
        print(f"{key}: {value}")