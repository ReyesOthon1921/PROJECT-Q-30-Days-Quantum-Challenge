"""
greedy_solver.py

Phase 7 first solver layer.

This module provides a simple greedy baseline solver for the stem-based QUBO.

Goal:
    Select favorable RNA stem candidates while avoiding overlapping or crossing stems.
"""

from src.classical.sequence_tools import clean_sequence
from src.classical.dotbracket import pairs_to_dotbracket
from src.qubo.candidate_stems import generate_candidate_stems
from src.qubo.build_qubo import stem_score, stems_overlap, stems_cross, build_stem_qubo


def solve_stem_qubo_greedy(sequence: str) -> dict:
    """
    Greedy baseline solver for the stem-based QUBO.

    This is not the final quantum solver.
    It is a classical baseline used before simulated annealing, QAOA, or VQE.
    """
    cleaned = clean_sequence(sequence)

    qubo = build_stem_qubo(cleaned)
    stems = generate_candidate_stems(cleaned)

    scored_stems = []

    for stem in stems:
        scored_stem = dict(stem)
        scored_stem["linear_score"] = stem_score(stem)
        scored_stems.append(scored_stem)

    # More negative score is better because QUBO is minimized.
    scored_stems.sort(
        key=lambda item: (
            item["linear_score"],
            -item["length"],
            item["stem_index"],
        )
    )

    selected_stems = []
    rejected_stems = []

    for stem in scored_stems:
        conflicts = []

        for chosen in selected_stems:
            if stems_overlap(stem, chosen):
                conflicts.append(
                    {
                        "with": chosen["variable_name"],
                        "reason": "overlap",
                    }
                )

            if stems_cross(stem, chosen):
                conflicts.append(
                    {
                        "with": chosen["variable_name"],
                        "reason": "crossing",
                    }
                )

        if conflicts:
            if len(rejected_stems) < 10:
                rejected_stems.append(
                    {
                        "variable_name": stem["variable_name"],
                        "linear_score": stem["linear_score"],
                        "conflicts": conflicts[:3],
                    }
                )
            continue

        selected_stems.append(stem)

    selected_pairs = []

    for stem in selected_stems:
        for pair in stem["pairs"]:
            selected_pairs.append(tuple(pair))

    selected_pairs = sorted(set(selected_pairs), key=lambda pair: (pair[0], pair[1]))

    if selected_pairs:
        predicted_structure = pairs_to_dotbracket(len(cleaned), selected_pairs)
    else:
        predicted_structure = "." * len(cleaned)

    objective_score = round(
        sum(stem["linear_score"] for stem in selected_stems),
        3,
    )

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "solver": "greedy stem-QUBO baseline",
        "qubo_model": qubo["model"],
        "total_candidate_stems": len(stems),
        "total_qubo_variables": qubo["num_variables"],
        "total_quadratic_penalties": qubo["num_quadratic_terms"],
        "selected_stem_count": len(selected_stems),
        "selected_pair_count": len(selected_pairs),
        "objective_score": objective_score,
        "predicted_structure": predicted_structure,
        "selected_stems": selected_stems,
        "selected_pairs": selected_pairs,
        "first_10_rejected_stems": rejected_stems,
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = solve_stem_qubo_greedy(sequence)

    print("Greedy stem-QUBO solver summary")
    print("-------------------------------")
    print(f"sequence: {result['sequence']}")
    print(f"length: {result['length']}")
    print(f"solver: {result['solver']}")
    print(f"total_candidate_stems: {result['total_candidate_stems']}")
    print(f"total_qubo_variables: {result['total_qubo_variables']}")
    print(f"total_quadratic_penalties: {result['total_quadratic_penalties']}")
    print(f"selected_stem_count: {result['selected_stem_count']}")
    print(f"selected_pair_count: {result['selected_pair_count']}")
    print(f"objective_score: {result['objective_score']}")
    print(f"predicted_structure: {result['predicted_structure']}")
    print(f"selected_pairs: {result['selected_pairs']}")