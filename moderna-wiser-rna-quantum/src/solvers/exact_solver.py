"""Exact enumerator for the project's existing stem-based QUBO model."""

from __future__ import annotations

import itertools
import time
from typing import Any, Sequence

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.simulated_annealing import (
    calculate_qubo_energy,
    decode_solution_to_structure,
)


def solve_stem_qubo_exact(
    sequence: str,
    max_variables: int = 20,
    min_stem_length: int = 2,
    min_loop_length: int = 3,
    allow_wobble: bool = True,
    overlap_penalty: float = 10.0,
    crossing_penalty: float = 8.0,
) -> dict[str, Any]:
    """Enumerate every binary assignment when the model is small enough."""

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
    variable_names = list(qubo["linear_terms"].keys())
    variable_count = len(variable_names)

    if variable_count > max_variables:
        return {
            "success": False,
            "skipped": True,
            "status": "skipped",
            "error": (
                f"Exact solver skipped because {variable_count} variables exceed "
                f"the configured limit of {max_variables}."
            ),
            "sequence": cleaned,
            "length": len(cleaned),
            "solver": "exact stem-QUBO enumeration",
            "runtime_seconds": round(time.perf_counter() - started, 6),
            "total_candidate_stems": variable_count,
            "total_qubo_variables": variable_count,
            "total_quadratic_penalties": len(qubo["quadratic_terms"]),
            "assignments_evaluated": 0,
            "best_energy": None,
            "best_solution": {},
            "predicted_structure": None,
            "selected_pairs": [],
            "selected_stems": [],
            "selected_stem_count": 0,
            "selected_pair_count": 0,
            "is_conflict_free": None,
            "structure_error": None,
        }

    best_energy: float | None = None
    best_solution: dict[str, int] = {name: 0 for name in variable_names}
    assignments_evaluated = 0

    for bits in itertools.product((0, 1), repeat=variable_count):
        assignments_evaluated += 1
        solution = dict(zip(variable_names, bits))
        energy = calculate_qubo_energy(
            solution,
            qubo["linear_terms"],
            qubo["quadratic_terms"],
        )
        if best_energy is None or energy < best_energy - 1e-12:
            best_energy = energy
            best_solution = solution

    decoded = decode_solution_to_structure(cleaned, stems, best_solution)

    return {
        "success": True,
        "skipped": False,
        "status": "success",
        "error": None,
        "sequence": cleaned,
        "length": len(cleaned),
        "solver": "exact stem-QUBO enumeration",
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "total_candidate_stems": variable_count,
        "total_qubo_variables": variable_count,
        "total_quadratic_penalties": len(qubo["quadratic_terms"]),
        "assignments_evaluated": assignments_evaluated,
        "best_energy": float(best_energy or 0.0),
        "best_solution": best_solution,
        "predicted_structure": decoded["predicted_structure"],
        "selected_pairs": decoded["selected_pairs"],
        "selected_stems": decoded["selected_stems"],
        "selected_stem_count": decoded["selected_stem_count"],
        "selected_pair_count": decoded["selected_pair_count"],
        "is_conflict_free": decoded["is_conflict_free"],
        "structure_error": decoded["structure_error"],
    }
