"""Regression tests for the Phase 50A greedy-solution mapping fix."""

from src.evaluation.phase50_solver_diagnostics import energy_decomposition
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import calculate_qubo_energy


def _run(sequence: str) -> tuple[dict, dict]:
    settings = {
        "min_stem_length": 2,
        "min_loop_length": 3,
        "allow_wobble": True,
        "overlap_penalty": 14.0,
        "crossing_penalty": 12.0,
    }
    result = solve_stem_qubo_greedy(sequence, **settings)
    qubo = build_stem_qubo(sequence, **settings)
    return result, qubo


def test_best_solution_matches_selected_stem_names() -> None:
    result, _ = _run("GGUGGGUGGCCAGCAGUU")
    selected_names = {stem["variable_name"] for stem in result["selected_stems"]}
    solution_names = {
        name for name, selected in result["best_solution"].items() if selected
    }

    assert selected_names
    assert solution_names == selected_names
    assert sum(result["best_solution"].values()) == result["selected_stem_count"]


def test_best_solution_energy_matches_reported_greedy_energy() -> None:
    result, qubo = _run("GGUGGGUGGCCAGCAGUU")
    recomputed = calculate_qubo_energy(
        result["best_solution"],
        qubo["linear_terms"],
        qubo["quadratic_terms"],
    )

    assert recomputed == result["best_energy"]
    assert recomputed == result["objective_score"]


def test_phase50_decomposition_reports_nonzero_greedy_selection() -> None:
    result, qubo = _run("GCGGCCGAAACGGCCG")
    decomposition = energy_decomposition(qubo, result["best_solution"])

    assert decomposition["selected_variable_count"] == result["selected_stem_count"]
    assert decomposition["selected_variable_count"] > 0
    assert decomposition["total_energy"] == result["best_energy"]
    assert decomposition["linear_reward"] == result["best_energy"]
    assert decomposition["quadratic_penalty"] == 0.0
