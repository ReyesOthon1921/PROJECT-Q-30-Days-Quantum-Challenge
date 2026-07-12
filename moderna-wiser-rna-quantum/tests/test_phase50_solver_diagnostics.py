from __future__ import annotations

from src.evaluation.phase50_solver_diagnostics import (
    build_adjacency,
    diagnose_sequence,
    flip_delta,
    one_flip_descent,
)
from src.solvers.simulated_annealing import calculate_qubo_energy


def test_flip_delta_matches_full_energy():
    variables = ["s_0", "s_1", "s_2"]
    linear_terms = {"s_0": -3.0, "s_1": -2.0, "s_2": -1.0}
    quadratic_terms = [
        {"var_a": "s_0", "var_b": "s_1", "coefficient": 5.0, "reasons": ["overlap"]},
        {"var_a": "s_1", "var_b": "s_2", "coefficient": 4.0, "reasons": ["crossing"]},
    ]
    linear, adjacency = build_adjacency(variables, linear_terms, quadratic_terms)
    state = [1, 0, 1]
    before = calculate_qubo_energy(dict(zip(variables, state)), linear_terms, quadratic_terms)
    delta = flip_delta(1, state, linear, adjacency)
    after_state = [1, 1, 1]
    after = calculate_qubo_energy(dict(zip(variables, after_state)), linear_terms, quadratic_terms)
    assert abs((after-before)-delta) < 1e-9


def test_one_flip_descent_never_increases_energy():
    variables = ["s_0", "s_1"]
    linear_terms = {"s_0": -3.0, "s_1": -2.0}
    quadratic_terms = [{"var_a":"s_0","var_b":"s_1","coefficient":10.0,"reasons":["overlap"]}]
    linear, adjacency = build_adjacency(variables, linear_terms, quadratic_terms)
    initial = [1, 1]
    refined, flips = one_flip_descent(initial, linear, adjacency)
    before = calculate_qubo_energy(dict(zip(variables, initial)), linear_terms, quadratic_terms)
    after = calculate_qubo_energy(dict(zip(variables, refined)), linear_terms, quadratic_terms)
    assert flips >= 1
    assert after <= before


def test_diagnosis_confirms_objective_failure_when_exact_is_wrong():
    result = diagnose_sequence("success", 0.4, 0.4, 0.4, -10.0, -10.0, -10.0, 1, 1.0, 1e-9)
    assert result == "objective_limitation_confirmed_small_qubo"


def test_diagnosis_confirms_solver_failure_when_exact_is_good_but_solver_misses():
    result = diagnose_sequence("success", 1.0, 0.5, 0.5, -12.0, -10.0, -11.0, 3, 0.5, 1e-9)
    assert result == "solver_limitation_confirmed_small_qubo"


def test_large_qubo_instability_label():
    result = diagnose_sequence("skipped", None, None, 0.7, None, -10.0, -11.0, 4, 0.4, 1e-9)
    assert result == "solver_instability_large_qubo"
