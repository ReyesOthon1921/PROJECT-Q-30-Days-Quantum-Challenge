"""
qaoa_prototype.py

Phase 16 QAOA readiness prototype.

This module does not claim quantum advantage.
It prepares a small QUBO subset that can later be passed into QAOA.

Current purpose:
1. Build QAOA-ready QUBO terms.
2. Limit to a small number of variables for near-term simulation.
3. Run exact search on the small subset as a correctness baseline.
4. Report estimated qubits and selected variables.
"""

from itertools import product

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo


def build_small_qaoa_problem(sequence: str, max_variables: int = 10) -> dict:
    """
    Build a small QAOA-ready QUBO subset.

    This keeps only the first max_variables QUBO variables so the problem is
    small enough for exact checking and later toy QAOA simulation.
    """
    cleaned = clean_sequence(sequence)
    qubo = build_stem_qubo(cleaned)

    all_variables = list(qubo["linear_terms"].keys())
    selected_variables = all_variables[:max_variables]
    selected_set = set(selected_variables)

    linear_terms = {
        variable: coefficient
        for variable, coefficient in qubo["linear_terms"].items()
        if variable in selected_set
    }

    quadratic_terms = []

    for term in qubo["first_20_quadratic_terms"]:
        if term["var_a"] in selected_set and term["var_b"] in selected_set:
            quadratic_terms.append(term)

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "source_model": qubo["model"],
        "qaoa_status": "QAOA-ready small QUBO subset",
        "note": "This is a QAOA preparation layer, not a full QAOA quantum run yet.",
        "original_qubo_variables": qubo["num_variables"],
        "original_estimated_qubits": qubo["estimated_qubits"],
        "selected_variable_count": len(selected_variables),
        "selected_variables": selected_variables,
        "linear_terms": linear_terms,
        "quadratic_terms": quadratic_terms,
        "estimated_qaoa_qubits": len(selected_variables),
        "suggested_next_step": "Use these terms to build a QAOA circuit with Qiskit or PennyLane.",
    }


def calculate_subset_energy(solution: dict, linear_terms: dict, quadratic_terms: list) -> float:
    """
    Calculate QUBO energy for the small QAOA subset.
    """
    energy = 0.0

    for variable, coefficient in linear_terms.items():
        energy += coefficient * solution.get(variable, 0)

    for term in quadratic_terms:
        energy += (
            term["coefficient"]
            * solution.get(term["var_a"], 0)
            * solution.get(term["var_b"], 0)
        )

    return round(energy, 6)


def exact_solve_small_qaoa_problem(problem: dict) -> dict:
    """
    Exact solve the small QUBO subset.

    This is used only as a baseline for the future QAOA prototype.
    """
    variables = problem["selected_variables"]
    linear_terms = problem["linear_terms"]
    quadratic_terms = problem["quadratic_terms"]

    if len(variables) > 16:
        return {
            "success": False,
            "error": "Too many variables for exact search. Reduce max_variables.",
            "variable_count": len(variables),
        }

    best_energy = None
    best_solution = None

    for bits in product([0, 1], repeat=len(variables)):
        solution = {
            variable: bit
            for variable, bit in zip(variables, bits)
        }

        energy = calculate_subset_energy(
            solution,
            linear_terms,
            quadratic_terms,
        )

        if best_energy is None or energy < best_energy:
            best_energy = energy
            best_solution = solution

    selected_variables = [
        variable
        for variable, bit in best_solution.items()
        if bit == 1
    ]

    return {
        "success": True,
        "solver": "exact search on QAOA-ready subset",
        "variable_count": len(variables),
        "best_energy": best_energy,
        "best_solution": best_solution,
        "selected_variables": selected_variables,
        "selected_variable_count": len(selected_variables),
    }


def run_qaoa_readiness_demo(sequence: str, max_variables: int = 10) -> dict:
    """
    Build and solve a small QAOA-ready QUBO subset.
    """
    problem = build_small_qaoa_problem(sequence, max_variables=max_variables)
    exact_result = exact_solve_small_qaoa_problem(problem)

    return {
        "success": True,
        "phase": "Phase 16 — QAOA readiness prototype",
        "problem": problem,
        "exact_subset_baseline": exact_result,
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_qaoa_readiness_demo(sequence)

    print("QAOA readiness prototype summary")
    print("--------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"original_qubo_variables: {result['problem']['original_qubo_variables']}")
    print(f"selected_variable_count: {result['problem']['selected_variable_count']}")
    print(f"estimated_qaoa_qubits: {result['problem']['estimated_qaoa_qubits']}")
    print(f"best_energy: {result['exact_subset_baseline']['best_energy']}")
    print(f"selected_variables: {result['exact_subset_baseline']['selected_variables']}")