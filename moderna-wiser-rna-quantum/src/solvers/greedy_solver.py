"""
greedy_solver.py

Phase 7 classical greedy baseline for the project's stem-based QUBO.
Phase 48 adds optional model settings, standardized energy, runtime, and status
fields while preserving the original default behavior and output keys.
"""

import time

from src.classical.sequence_tools import clean_sequence
from src.classical.dotbracket import pairs_to_dotbracket
from src.qubo.build_qubo import build_stem_qubo, stem_score, stems_cross, stems_overlap


def solve_stem_qubo_greedy(
    sequence: str,
    min_stem_length: int = 2,
    min_loop_length: int = 3,
    allow_wobble: bool = True,
    overlap_penalty: float = 10.0,
    crossing_penalty: float = 8.0,
) -> dict:
    """Select favorable, mutually compatible stems greedily."""

    started = time.perf_counter()
    cleaned = clean_sequence(sequence)
    qubo = build_stem_qubo(
        cleaned,
        overlap_penalty=overlap_penalty,
        crossing_penalty=crossing_penalty,
        min_stem_length=min_stem_length,
        min_loop_length=min_loop_length,
        allow_wobble=allow_wobble,
    )
    stems = qubo["stems"]

    scored_stems = []
    for stem in stems:
        scored_stem = dict(stem)
        scored_stem["linear_score"] = stem_score(stem)
        scored_stems.append(scored_stem)

    # More negative is better because the QUBO is minimized.
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
                conflicts.append({"with": chosen["variable_name"], "reason": "overlap"})
            if stems_cross(stem, chosen):
                conflicts.append({"with": chosen["variable_name"], "reason": "crossing"})

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

    selected_pairs = sorted(
        {tuple(pair) for stem in selected_stems for pair in stem["pairs"]},
        key=lambda pair: (pair[0], pair[1]),
    )
    predicted_structure = (
        pairs_to_dotbracket(len(cleaned), selected_pairs)
        if selected_pairs
        else "." * len(cleaned)
    )

    # ``selected_stems`` contains scored copies of the original stem dictionaries.
    # Comparing the original dictionaries directly against those copies is unsafe
    # because the copies include the extra ``linear_score`` field. Track selection
    # by the stable QUBO variable name so ``best_solution`` matches the prediction.
    selected_variable_names = {
        stem["variable_name"] for stem in selected_stems
    }
    best_solution = {
        stem["variable_name"]: int(
            stem["variable_name"] in selected_variable_names
        )
        for stem in stems
    }
    # Selected stems are conflict-free, so the quadratic penalty contribution is 0.
    objective_score = round(sum(stem["linear_score"] for stem in selected_stems), 6)

    return {
        "success": True,
        "status": "success",
        "error": None,
        "sequence": cleaned,
        "length": len(cleaned),
        "solver": "greedy stem-QUBO baseline",
        "qubo_model": qubo["model"],
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "total_candidate_stems": len(stems),
        "total_qubo_variables": qubo["num_variables"],
        "total_quadratic_penalties": qubo["num_quadratic_terms"],
        "selected_stem_count": len(selected_stems),
        "selected_pair_count": len(selected_pairs),
        "objective_score": objective_score,
        "best_energy": objective_score,
        "best_solution": best_solution,
        "predicted_structure": predicted_structure,
        "selected_stems": selected_stems,
        "selected_pairs": selected_pairs,
        "is_conflict_free": True,
        "structure_error": None,
        "first_10_rejected_stems": rejected_stems,
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = solve_stem_qubo_greedy(sequence)
    for key, value in result.items():
        print(f"{key}: {value}")
