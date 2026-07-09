"""
build_qubo.py

Phase 6 QUBO formulation.

This module builds a simple stem-based QUBO for RNA secondary-structure
candidate selection.

QUBO idea:
    minimize objective

    favorable stems get negative linear weights
    invalid combinations get positive penalty weights
"""

from src.classical.sequence_tools import clean_sequence
from src.qubo.candidate_stems import generate_candidate_stems


PAIR_REWARDS = {
    "G-C": -3.0,
    "C-G": -3.0,
    "A-U": -2.0,
    "U-A": -2.0,
    "G-U wobble": -1.0,
    "U-G wobble": -1.0,
}


def stem_score(stem: dict) -> float:
    """
    Convert a stem into a linear QUBO score.

    More stable stems receive more negative values because QUBO minimizes.
    """
    score = 0.0

    for pair_type in stem["pair_types"]:
        score += PAIR_REWARDS.get(pair_type, 0.0)

    return score


def stem_base_positions(stem: dict) -> set:
    """
    Return every nucleotide index used by a stem.
    """
    positions = set()

    for i, j in stem["pairs"]:
        positions.add(i)
        positions.add(j)

    return positions


def stems_overlap(stem_a: dict, stem_b: dict) -> bool:
    """
    Return True if two stems reuse any nucleotide position.
    """
    return len(stem_base_positions(stem_a) & stem_base_positions(stem_b)) > 0


def pairs_cross(pair_a: tuple, pair_b: tuple) -> bool:
    """
    Detect crossing base pairs.

    Crossing example:
        i < k < j < l
    """
    i, j = pair_a
    k, l = pair_b

    return (i < k < j < l) or (k < i < l < j)


def stems_cross(stem_a: dict, stem_b: dict) -> bool:
    """
    Return True if any pair from stem A crosses any pair from stem B.
    """
    for pair_a in stem_a["pairs"]:
        for pair_b in stem_b["pairs"]:
            if pairs_cross(pair_a, pair_b):
                return True

    return False


def build_stem_qubo(
    sequence: str,
    overlap_penalty: float = 10.0,
    crossing_penalty: float = 8.0,
) -> dict:
    """
    Build a stem-based QUBO dictionary.

    Linear terms:
        Q[i, i]

    Quadratic terms:
        Q[i, j] for invalid stem combinations
    """
    cleaned = clean_sequence(sequence)
    stems = generate_candidate_stems(cleaned)

    linear_terms = {}
    quadratic_terms = []

    for stem in stems:
        variable = stem["variable_name"]
        linear_terms[variable] = stem_score(stem)

    for index_a in range(len(stems)):
        for index_b in range(index_a + 1, len(stems)):
            stem_a = stems[index_a]
            stem_b = stems[index_b]

            penalty = 0.0
            reasons = []

            if stems_overlap(stem_a, stem_b):
                penalty += overlap_penalty
                reasons.append("overlap")

            if stems_cross(stem_a, stem_b):
                penalty += crossing_penalty
                reasons.append("crossing")

            if penalty > 0:
                quadratic_terms.append(
                    {
                        "var_a": stem_a["variable_name"],
                        "var_b": stem_b["variable_name"],
                        "coefficient": penalty,
                        "reasons": reasons,
                    }
                )

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "model": "stem-based QUBO",
        "objective": "minimize",
        "num_variables": len(stems),
        "estimated_qubits": len(stems),
        "num_linear_terms": len(linear_terms),
        "num_quadratic_terms": len(quadratic_terms),
        "linear_terms": linear_terms,
        "first_20_quadratic_terms": quadratic_terms[:20],
        "first_10_stems": stems[:10],
        "penalty_settings": {
            "overlap_penalty": overlap_penalty,
            "crossing_penalty": crossing_penalty,
        },
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    qubo = build_stem_qubo(sequence)

    print("Stem-based QUBO summary")
    print("-----------------------")
    print(f"sequence: {qubo['sequence']}")
    print(f"length: {qubo['length']}")
    print(f"model: {qubo['model']}")
    print(f"num_variables: {qubo['num_variables']}")
    print(f"estimated_qubits: {qubo['estimated_qubits']}")
    print(f"num_linear_terms: {qubo['num_linear_terms']}")
    print(f"num_quadratic_terms: {qubo['num_quadratic_terms']}")
    print(f"penalty_settings: {qubo['penalty_settings']}")
    print(f"first_10_linear_terms: {list(qubo['linear_terms'].items())[:10]}")
    print(f"first_5_quadratic_terms: {qubo['first_20_quadratic_terms'][:5]}")