"""Objective variants for Phase 50B RNA stem-QUBO ablation experiments.

The original Phase 49/50A QUBO remains untouched. This module creates
backward-compatible copies of that QUBO with controlled changes to the linear
stem rewards so each objective term can be evaluated independently.
"""

from __future__ import annotations

import itertools
import math
import time
from typing import Any

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import PAIR_REWARDS, build_stem_qubo
from src.solvers.simulated_annealing import (
    calculate_qubo_energy,
    decode_solution_to_structure,
)

SUPPORTED_REWARD_MODES = {"sum", "mean_pair", "sqrt_length"}


def normalize_pair_rewards(raw: dict[str, Any] | None = None) -> dict[str, float]:
    """Return a complete numeric pair-reward mapping."""

    rewards = {key: float(value) for key, value in PAIR_REWARDS.items()}
    if raw:
        for key, value in raw.items():
            if key not in rewards:
                raise ValueError(f"Unsupported pair reward key: {key}")
            rewards[key] = float(value)
    return rewards


def validate_objective_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a Phase 50B objective configuration."""

    mode = str(settings.get("reward_mode", "sum")).strip().lower()
    if mode not in SUPPORTED_REWARD_MODES:
        raise ValueError(
            f"Unsupported reward_mode {mode!r}; expected one of "
            f"{sorted(SUPPORTED_REWARD_MODES)}."
        )
    short_length = int(settings.get("short_stem_length", 2))
    if short_length < 1:
        raise ValueError("short_stem_length must be at least 1.")
    return {
        "reward_mode": mode,
        "short_stem_penalty": float(settings.get("short_stem_penalty", 0.0)),
        "short_stem_length": short_length,
        "pair_rewards": normalize_pair_rewards(settings.get("pair_rewards")),
    }


def score_stem_variant(stem: dict[str, Any], settings: dict[str, Any]) -> float:
    """Compute one controlled linear stem score.

    All rewards are minimization coefficients. More negative values are more
    favorable. A positive short-stem penalty therefore reduces the preference
    for the configured short-stem length.
    """

    normalized = validate_objective_settings(settings)
    length = int(stem.get("length", len(stem.get("pair_types", []))))
    if length <= 0:
        raise ValueError("Stem length must be positive.")
    base_sum = sum(
        normalized["pair_rewards"].get(str(pair_type), 0.0)
        for pair_type in stem.get("pair_types", [])
    )
    mode = normalized["reward_mode"]
    if mode == "sum":
        score = base_sum
    elif mode == "mean_pair":
        score = base_sum / length
    else:  # sqrt_length
        score = base_sum / math.sqrt(length)
    if length == normalized["short_stem_length"]:
        score += normalized["short_stem_penalty"]
    return round(float(score), 12)


def build_variant_qubo(
    sequence: str,
    strict_config: dict[str, Any],
    objective_settings: dict[str, Any],
) -> dict[str, Any]:
    """Build the existing QUBO and replace only its linear reward terms."""

    objective = validate_objective_settings(objective_settings)
    min_stem_length = int(
        objective_settings.get(
            "min_stem_length",
            strict_config.get("stem_min_length", 2),
        )
    )
    qubo = build_stem_qubo(
        sequence,
        overlap_penalty=float(strict_config.get("overlap_penalty", 14.0)),
        crossing_penalty=float(strict_config.get("crossing_penalty", 12.0)),
        min_stem_length=min_stem_length,
        min_loop_length=int(strict_config.get("min_loop_length", 3)),
        allow_wobble=bool(strict_config.get("allow_wobble", True)),
    )
    qubo = dict(qubo)
    qubo["linear_terms"] = {
        stem["variable_name"]: score_stem_variant(stem, objective)
        for stem in qubo["stems"]
    }
    qubo["num_linear_terms"] = len(qubo["linear_terms"])
    qubo["objective_settings"] = {
        **objective,
        "min_stem_length": min_stem_length,
    }
    qubo["candidate_settings"] = {
        **dict(qubo.get("candidate_settings", {})),
        "min_stem_length": min_stem_length,
    }
    return qubo


def solve_variant_qubo_exact(
    sequence: str,
    qubo: dict[str, Any],
    max_variables: int = 20,
    *,
    collect_optimal_structures: bool = False,
    max_optimal_structures: int = 2048,
) -> dict[str, Any]:
    """Exactly enumerate a supplied objective-variant QUBO when feasible.

    ``collect_optimal_structures`` enables a tie-aware audit of the exact
    optimum. The original deterministic representative solution is preserved
    for backward compatibility, while the additional fields record how many
    assignments share the minimum and which distinct structures were captured.
    Capturing is bounded so a highly degenerate QUBO cannot exhaust memory.
    """

    started = time.perf_counter()
    cleaned = clean_sequence(sequence)
    variable_names = list(qubo["linear_terms"].keys())
    if max_optimal_structures < 1:
        raise ValueError("max_optimal_structures must be at least 1.")
    if len(variable_names) > int(max_variables):
        return {
            "status": "skipped",
            "success": False,
            "skipped": True,
            "error": (
                f"Exact solver skipped because {len(variable_names)} variables "
                f"exceed the configured limit of {max_variables}."
            ),
            "best_energy": None,
            "best_solution": {},
            "predicted_structure": None,
            "selected_stem_count": 0,
            "runtime_seconds": round(time.perf_counter() - started, 6),
            "assignments_evaluated": 0,
            "optimal_assignment_count": 0,
            "captured_optimal_structure_count": 0,
            "optimal_structures": [],
            "optimal_structures_truncated": False,
        }

    tolerance = 1.0e-12
    best_energy: float | None = None
    best_solution = {name: 0 for name in variable_names}
    assignments = 0
    optimal_assignment_count = 0
    optimal_structures: dict[str, int] = {}
    optimal_structures_truncated = False

    def record_optimal_structure(solution: dict[str, int]) -> None:
        nonlocal optimal_structures_truncated
        if not collect_optimal_structures:
            return
        decoded = decode_solution_to_structure(cleaned, qubo["stems"], solution)
        structure = decoded.get("predicted_structure")
        if structure is None:
            structure = f"<invalid:{decoded.get('structure_error') or 'unknown'}>"
        structure = str(structure)
        if structure in optimal_structures:
            optimal_structures[structure] += 1
            return
        if len(optimal_structures) >= int(max_optimal_structures):
            optimal_structures_truncated = True
            return
        optimal_structures[structure] = 1

    for bits in itertools.product((0, 1), repeat=len(variable_names)):
        assignments += 1
        solution = dict(zip(variable_names, bits))
        energy = calculate_qubo_energy(
            solution,
            qubo["linear_terms"],
            qubo["quadratic_terms"],
        )
        if best_energy is None or energy < best_energy - tolerance:
            best_energy = float(energy)
            best_solution = solution
            optimal_assignment_count = 1
            optimal_structures = {}
            optimal_structures_truncated = False
            record_optimal_structure(solution)
        elif abs(float(energy) - float(best_energy)) <= tolerance:
            optimal_assignment_count += 1
            record_optimal_structure(solution)

    decoded = decode_solution_to_structure(cleaned, qubo["stems"], best_solution)
    captured = [
        {"structure": structure, "assignment_count": count}
        for structure, count in sorted(optimal_structures.items())
    ]
    return {
        "status": "success",
        "success": True,
        "skipped": False,
        "error": None,
        "best_energy": float(best_energy or 0.0),
        "best_solution": best_solution,
        "predicted_structure": decoded.get("predicted_structure"),
        "selected_stem_count": decoded.get("selected_stem_count"),
        "is_conflict_free": decoded.get("is_conflict_free"),
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "assignments_evaluated": assignments,
        "optimal_assignment_count": optimal_assignment_count,
        "captured_optimal_structure_count": len(captured),
        "optimal_structures": captured,
        "optimal_structures_truncated": optimal_structures_truncated,
    }


def solve_variant_qubo_greedy(
    sequence: str,
    qubo: dict[str, Any],
) -> dict[str, Any]:
    """Greedily select negative-reward, mutually compatible variant stems."""

    started = time.perf_counter()
    cleaned = clean_sequence(sequence)
    conflicts: dict[str, set[str]] = {
        name: set() for name in qubo["linear_terms"]
    }
    for term in qubo["quadratic_terms"]:
        left = str(term["var_a"])
        right = str(term["var_b"])
        conflicts[left].add(right)
        conflicts[right].add(left)
    stems_by_name = {stem["variable_name"]: stem for stem in qubo["stems"]}
    ordered = sorted(
        qubo["linear_terms"],
        key=lambda name: (
            float(qubo["linear_terms"][name]),
            -int(stems_by_name[name]["length"]),
            int(stems_by_name[name]["stem_index"]),
        ),
    )
    selected: list[str] = []
    for name in ordered:
        coefficient = float(qubo["linear_terms"][name])
        if coefficient >= -1.0e-12:
            continue
        if any(chosen in conflicts[name] for chosen in selected):
            continue
        selected.append(name)
    solution = {
        name: int(name in selected)
        for name in qubo["linear_terms"]
    }
    energy = calculate_qubo_energy(
        solution,
        qubo["linear_terms"],
        qubo["quadratic_terms"],
    )
    decoded = decode_solution_to_structure(cleaned, qubo["stems"], solution)
    return {
        "status": "success",
        "success": True,
        "error": None,
        "best_energy": float(energy),
        "best_solution": solution,
        "predicted_structure": decoded.get("predicted_structure"),
        "selected_stem_count": decoded.get("selected_stem_count"),
        "is_conflict_free": decoded.get("is_conflict_free"),
        "runtime_seconds": round(time.perf_counter() - started, 6),
    }
