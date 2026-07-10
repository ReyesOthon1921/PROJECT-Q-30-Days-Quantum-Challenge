"""
simulated_annealing.py

Phase 11 solver layer.

This module implements a simulated annealing baseline solver for the
stem-based RNA QUBO model.

Goal:
    Improve beyond the greedy baseline before adding QAOA or VQE.
"""

import math
import random
import time

from src.classical.sequence_tools import clean_sequence
from src.classical.dotbracket import pairs_to_dotbracket
from src.qubo.candidate_stems import generate_candidate_stems
from src.qubo.build_qubo import stem_score, stems_overlap, stems_cross


def build_solver_terms(
    stems: list,
    overlap_penalty: float = 10.0,
    crossing_penalty: float = 8.0,
) -> dict:
    """
    Build full linear and quadratic QUBO terms for the simulated annealer.
    """
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
        "linear_terms": linear_terms,
        "quadratic_terms": quadratic_terms,
        "overlap_penalty": overlap_penalty,
        "crossing_penalty": crossing_penalty,
    }


def calculate_qubo_energy(
    solution: dict,
    linear_terms: dict,
    quadratic_terms: list,
) -> float:
    """
    Calculate QUBO objective value for a binary solution.
    """
    energy = 0.0

    for variable, coefficient in linear_terms.items():
        energy += coefficient * solution.get(variable, 0)

    for term in quadratic_terms:
        var_a = term["var_a"]
        var_b = term["var_b"]
        coefficient = term["coefficient"]

        energy += coefficient * solution.get(var_a, 0) * solution.get(var_b, 0)

    return round(energy, 6)


def create_initial_solution(variable_names: list) -> dict:
    """
    Start from an empty RNA structure.
    """
    return {variable: 0 for variable in variable_names}


def selected_stems_from_solution(stems: list, solution: dict) -> list:
    """
    Return stems selected by a binary solution.
    """
    selected = []

    for stem in stems:
        variable = stem["variable_name"]

        if solution.get(variable, 0) == 1:
            selected_stem = dict(stem)
            selected_stem["linear_score"] = stem_score(stem)
            selected.append(selected_stem)

    return selected


def detect_selected_conflicts(selected_stems: list) -> list:
    """
    Detect overlap or crossing conflicts in selected stems.
    """
    conflicts = []

    for index_a in range(len(selected_stems)):
        for index_b in range(index_a + 1, len(selected_stems)):
            stem_a = selected_stems[index_a]
            stem_b = selected_stems[index_b]

            reasons = []

            if stems_overlap(stem_a, stem_b):
                reasons.append("overlap")

            if stems_cross(stem_a, stem_b):
                reasons.append("crossing")

            if reasons:
                conflicts.append(
                    {
                        "stem_a": stem_a["variable_name"],
                        "stem_b": stem_b["variable_name"],
                        "reasons": reasons,
                    }
                )

    return conflicts


def decode_solution_to_structure(sequence: str, stems: list, solution: dict) -> dict:
    """
    Decode selected stems into base pairs and dot-bracket notation.
    """
    cleaned = clean_sequence(sequence)
    selected_stems = selected_stems_from_solution(stems, solution)
    conflicts = detect_selected_conflicts(selected_stems)

    selected_pairs = []

    for stem in selected_stems:
        for pair in stem["pairs"]:
            selected_pairs.append(tuple(pair))

    selected_pairs = sorted(set(selected_pairs), key=lambda pair: (pair[0], pair[1]))

    predicted_structure = None
    structure_error = None

    try:
        if conflicts:
            structure_error = "Selected stems contain overlap or crossing conflicts."
        else:
            predicted_structure = pairs_to_dotbracket(len(cleaned), selected_pairs)

    except Exception as error:
        structure_error = str(error)

    return {
        "selected_stem_count": len(selected_stems),
        "selected_pair_count": len(selected_pairs),
        "selected_stems": selected_stems,
        "selected_pairs": selected_pairs,
        "is_conflict_free": len(conflicts) == 0,
        "first_10_conflicts": conflicts[:10],
        "predicted_structure": predicted_structure,
        "structure_error": structure_error,
    }


def solve_stem_qubo_simulated_annealing(
    sequence: str,
    num_steps: int = 8000,
    initial_temperature: float = 10.0,
    final_temperature: float = 0.01,
    cooling_rate: float = 0.995,
    seed: int = 7,
) -> dict:
    """
    Solve stem-based QUBO using simulated annealing.
    """
    cleaned = clean_sequence(sequence)
    stems = generate_candidate_stems(cleaned)

    if not stems:
        return {
            "success": False,
            "error": "No candidate stems were generated.",
            "sequence": cleaned,
            "length": len(cleaned),
        }

    solver_terms = build_solver_terms(stems)
    linear_terms = solver_terms["linear_terms"]
    quadratic_terms = solver_terms["quadratic_terms"]

    variable_names = list(linear_terms.keys())

    random_generator = random.Random(seed)

    current_solution = create_initial_solution(variable_names)
    current_energy = calculate_qubo_energy(
        current_solution,
        linear_terms,
        quadratic_terms,
    )

    best_solution = dict(current_solution)
    best_energy = current_energy

    temperature = initial_temperature
    accepted_moves = 0

    start_time = time.perf_counter()

    for _ in range(num_steps):
        variable = random_generator.choice(variable_names)

        candidate_solution = dict(current_solution)
        candidate_solution[variable] = 1 - candidate_solution[variable]

        candidate_energy = calculate_qubo_energy(
            candidate_solution,
            linear_terms,
            quadratic_terms,
        )

        delta_energy = candidate_energy - current_energy

        accept_move = False

        if delta_energy <= 0:
            accept_move = True
        else:
            acceptance_probability = math.exp(
                -delta_energy / max(temperature, 1e-9)
            )

            if random_generator.random() < acceptance_probability:
                accept_move = True

        if accept_move:
            current_solution = candidate_solution
            current_energy = candidate_energy
            accepted_moves += 1

            if current_energy < best_energy:
                best_solution = dict(current_solution)
                best_energy = current_energy

        temperature = max(final_temperature, temperature * cooling_rate)

    runtime_seconds = round(time.perf_counter() - start_time, 6)

    decoded = decode_solution_to_structure(cleaned, stems, best_solution)

    return {
        "success": True,
        "sequence": cleaned,
        "length": len(cleaned),
        "solver": "simulated annealing stem-QUBO baseline",
        "num_steps": num_steps,
        "initial_temperature": initial_temperature,
        "final_temperature": final_temperature,
        "cooling_rate": cooling_rate,
        "seed": seed,
        "accepted_moves": accepted_moves,
        "runtime_seconds": runtime_seconds,
        "total_candidate_stems": len(stems),
        "total_qubo_variables": len(variable_names),
        "total_quadratic_penalties": len(quadratic_terms),
        "best_energy": best_energy,
        "best_solution": best_solution,
        "selected_stem_count": decoded["selected_stem_count"],
        "selected_pair_count": decoded["selected_pair_count"],
        "predicted_structure": decoded["predicted_structure"],
        "is_conflict_free": decoded["is_conflict_free"],
        "structure_error": decoded["structure_error"],
        "selected_pairs": decoded["selected_pairs"],
        "selected_stems": decoded["selected_stems"],
        "first_10_conflicts": decoded["first_10_conflicts"],
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = solve_stem_qubo_simulated_annealing(sequence)

    print("Simulated annealing stem-QUBO solver summary")
    print("-------------------------------------------")
    print(f"success: {result['success']}")
    print(f"sequence: {result['sequence']}")
    print(f"length: {result['length']}")
    print(f"solver: {result['solver']}")
    print(f"total_candidate_stems: {result['total_candidate_stems']}")
    print(f"total_qubo_variables: {result['total_qubo_variables']}")
    print(f"total_quadratic_penalties: {result['total_quadratic_penalties']}")
    print(f"best_energy: {result['best_energy']}")
    print(f"selected_stem_count: {result['selected_stem_count']}")
    print(f"selected_pair_count: {result['selected_pair_count']}")
    print(f"is_conflict_free: {result['is_conflict_free']}")
    print(f"predicted_structure: {result['predicted_structure']}")
    print(f"selected_pairs: {result['selected_pairs']}")
    print(f"runtime_seconds: {result['runtime_seconds']}")