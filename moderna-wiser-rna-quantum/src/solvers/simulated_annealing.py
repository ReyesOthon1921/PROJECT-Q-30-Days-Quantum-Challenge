"""
simulated_annealing.py

Classical simulated-annealing baseline for the existing stem-based QUBO.
Phase 48 makes the candidate and penalty settings configurable while preserving
all original defaults and output fields.
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
    """Build complete linear and quadratic terms for the annealer."""

    linear_terms = {
        stem["variable_name"]: stem_score(stem)
        for stem in stems
    }
    quadratic_terms = []

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
    """Calculate the QUBO objective for a binary assignment."""

    energy = sum(
        coefficient * solution.get(variable, 0)
        for variable, coefficient in linear_terms.items()
    )
    energy += sum(
        term["coefficient"]
        * solution.get(term["var_a"], 0)
        * solution.get(term["var_b"], 0)
        for term in quadratic_terms
    )
    return round(float(energy), 6)


def create_initial_solution(variable_names: list) -> dict:
    return {variable: 0 for variable in variable_names}


def selected_stems_from_solution(stems: list, solution: dict) -> list:
    selected = []
    for stem in stems:
        if solution.get(stem["variable_name"], 0) == 1:
            selected_stem = dict(stem)
            selected_stem["linear_score"] = stem_score(stem)
            selected.append(selected_stem)
    return selected


def detect_selected_conflicts(selected_stems: list) -> list:
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
    cleaned = clean_sequence(sequence)
    selected_stems = selected_stems_from_solution(stems, solution)
    conflicts = detect_selected_conflicts(selected_stems)
    selected_pairs = sorted(
        {tuple(pair) for stem in selected_stems for pair in stem["pairs"]},
        key=lambda pair: (pair[0], pair[1]),
    )

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
    min_stem_length: int = 2,
    min_loop_length: int = 3,
    allow_wobble: bool = True,
    overlap_penalty: float = 10.0,
    crossing_penalty: float = 8.0,
) -> dict:
    """Solve the existing stem-QUBO with reproducible simulated annealing."""

    started = time.perf_counter()
    cleaned = clean_sequence(sequence)
    stems = generate_candidate_stems(
        cleaned,
        min_stem_length=min_stem_length,
        min_loop_length=min_loop_length,
        allow_wobble=allow_wobble,
    )
    solver_terms = build_solver_terms(stems, overlap_penalty, crossing_penalty)
    linear_terms = solver_terms["linear_terms"]
    quadratic_terms = solver_terms["quadratic_terms"]
    variable_names = list(linear_terms.keys())

    if not variable_names:
        return {
            "success": True,
            "status": "success",
            "error": None,
            "sequence": cleaned,
            "length": len(cleaned),
            "solver": "simulated annealing stem-QUBO baseline",
            "num_steps": 0,
            "initial_temperature": initial_temperature,
            "final_temperature": final_temperature,
            "cooling_rate": cooling_rate,
            "seed": seed,
            "accepted_moves": 0,
            "runtime_seconds": round(time.perf_counter() - started, 6),
            "total_candidate_stems": 0,
            "total_qubo_variables": 0,
            "total_quadratic_penalties": 0,
            "best_energy": 0.0,
            "best_solution": {},
            "selected_stem_count": 0,
            "selected_pair_count": 0,
            "predicted_structure": "." * len(cleaned),
            "is_conflict_free": True,
            "structure_error": None,
            "selected_pairs": [],
            "selected_stems": [],
            "first_10_conflicts": [],
        }

    random_generator = random.Random(seed)
    current_solution = create_initial_solution(variable_names)
    current_energy = calculate_qubo_energy(current_solution, linear_terms, quadratic_terms)
    best_solution = dict(current_solution)
    best_energy = current_energy
    temperature = initial_temperature
    accepted_moves = 0

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

        accept_move = delta_energy <= 0
        if not accept_move:
            acceptance_probability = math.exp(
                -delta_energy / max(temperature, 1e-9)
            )
            accept_move = random_generator.random() < acceptance_probability

        if accept_move:
            current_solution = candidate_solution
            current_energy = candidate_energy
            accepted_moves += 1
            if current_energy < best_energy:
                best_solution = dict(current_solution)
                best_energy = current_energy

        temperature = max(final_temperature, temperature * cooling_rate)

    decoded = decode_solution_to_structure(cleaned, stems, best_solution)

    return {
        "success": True,
        "status": "success",
        "error": None,
        "sequence": cleaned,
        "length": len(cleaned),
        "solver": "simulated annealing stem-QUBO baseline",
        "num_steps": num_steps,
        "initial_temperature": initial_temperature,
        "final_temperature": final_temperature,
        "cooling_rate": cooling_rate,
        "seed": seed,
        "accepted_moves": accepted_moves,
        "runtime_seconds": round(time.perf_counter() - started, 6),
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
    for key, value in result.items():
        print(f"{key}: {value}")
