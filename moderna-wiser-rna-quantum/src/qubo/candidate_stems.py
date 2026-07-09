"""
candidate_stems.py

Phase 5 QUBO preparation.

This module groups consecutive nested base pairs into stem candidates.

Example:
    s_0 = 1 means candidate stem 0 is selected.
    s_0 = 0 means candidate stem 0 is not selected.
"""

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence
from src.qubo.candidate_pairs import generate_candidate_pairs


def generate_candidate_stems(
    sequence: str,
    min_stem_length: int = 2,
    min_loop_length: int = 3,
    allow_wobble: bool = True,
) -> list:
    """
    Generate candidate RNA stems from candidate base pairs.

    A stem is a run of nested pairs:
        (i, j), (i+1, j-1), (i+2, j-2), ...
    """
    cleaned = clean_sequence(sequence)

    if not validate_rna_sequence(cleaned):
        raise ValueError("Invalid RNA sequence. Use only A, U, G, and C.")

    candidate_pairs = generate_candidate_pairs(
        cleaned,
        min_loop_length=min_loop_length,
        allow_wobble=allow_wobble,
    )

    pair_lookup = {
        (candidate["i"], candidate["j"]): candidate
        for candidate in candidate_pairs
    }

    stems = []
    stem_index = 0

    for i, j in pair_lookup:
        # Only start a stem if this pair is not continuing a previous stem.
        if (i - 1, j + 1) in pair_lookup:
            continue

        stem_pairs = []
        left = i
        right = j

        while (left, right) in pair_lookup:
            pair_data = pair_lookup[(left, right)]
            stem_pairs.append(pair_data)
            left += 1
            right -= 1

        if len(stem_pairs) >= min_stem_length:
            stems.append(
                {
                    "stem_index": stem_index,
                    "variable_name": f"s_{stem_index}",
                    "length": len(stem_pairs),
                    "start_pair": (stem_pairs[0]["i"], stem_pairs[0]["j"]),
                    "end_pair": (stem_pairs[-1]["i"], stem_pairs[-1]["j"]),
                    "pairs": [
                        (pair["i"], pair["j"])
                        for pair in stem_pairs
                    ],
                    "pair_types": [
                        pair["pair_type"]
                        for pair in stem_pairs
                    ],
                }
            )

            stem_index += 1

    return stems


def build_stem_index_map(stems: list) -> dict:
    """
    Map each stem to a QUBO variable name.
    """
    stem_index_map = {}

    for stem in stems:
        stem_index_map[tuple(stem["pairs"])] = stem["variable_name"]

    return stem_index_map


def summarize_candidate_stems(sequence: str) -> dict:
    """
    Return a summary of candidate stem variables.
    """
    cleaned = clean_sequence(sequence)
    stems = generate_candidate_stems(cleaned)
    stem_index_map = build_stem_index_map(stems)

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "candidate_stem_count": len(stems),
        "estimated_binary_variables": len(stems),
        "estimated_qubits": len(stems),
        "first_10_candidate_stems": stems[:10],
        "first_10_stem_index_map": list(stem_index_map.items())[:10],
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    summary = summarize_candidate_stems(sequence)

    print("Candidate stem summary")
    print("----------------------")
    for key, value in summary.items():
        print(f"{key}: {value}")