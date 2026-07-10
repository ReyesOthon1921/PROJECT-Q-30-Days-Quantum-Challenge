"""
vqe_prototype.py

Phase 17 VQE readiness prototype.

This module does not claim quantum advantage.
It prepares a small QUBO subset and converts it into a VQE-ready
Ising/Hamiltonian-style representation.

Current purpose:
1. Build a small QUBO subset.
2. Convert binary variables into spin-style terms.
3. Estimate VQE qubit requirements.
4. Run exact search as a baseline for the small subset.
"""

from itertools import product

from src.classical.sequence_tools import clean_sequence
from src.qubo.build_qubo import build_stem_qubo


def build_small_vqe_problem(sequence: str, max_variables: int = 10) -> dict:
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
        "vqe_status": "VQE-ready small Hamiltonian subset",
        "note": "This is a VQE preparation layer, not a full VQE quantum run yet.",
        "original_qubo_variables": qubo["num_variables"],
        "original_estimated_qubits": qubo["estimated_qubits"],
        "selected_variable_count": len(selected_variables),
        "selected_variables": selected_variables,
        "linear_terms": linear_terms,
        "quadratic_terms": quadratic_terms,
        "estimated_vqe_qubits": len(selected_variables),
    }


def qubo_to_ising_terms(problem: dict) -> dict:
    """
    Convert a QUBO subset into an Ising-style Hamiltonian representation.

    Binary variable x is mapped using:

    x = (1 - z) / 2

    This creates:
    - a constant energy offset
    - single-qubit Z terms
    - two-qubit ZZ interaction terms
    """
    linear_terms = problem["linear_terms"]
    quadratic_terms = problem["quadratic_terms"]

    constant = 0.0
    z_terms = {}
    zz_terms = []

    for variable, coefficient in linear_terms.items():
        constant += coefficient / 2
        z_terms[variable] = z_terms.get(variable, 0.0) - coefficient / 2

    for term in quadratic_terms:
        var_a = term["var_a"]
        var_b = term["var_b"]
        coefficient = term["coefficient"]

        constant += coefficient / 4
        z_terms[var_a] = z_terms.get(var_a, 0.0) - coefficient / 4
        z_terms[var_b] = z_terms.get(var_b, 0.0) - coefficient / 4

        zz_terms.append({
            "var_a": var_a,
            "var_b": var_b,
            "coefficient": round(coefficient / 4, 6),
        })

    rounded_z_terms = {
        variable: round(coefficient, 6)
        for variable, coefficient in z_terms.items()
    }

    return {
        "hamiltonian_type": "Ising-style Z and ZZ Hamiltonian",
        "constant_offset": round(constant, 6),
        "z_terms": rounded_z_terms,
        "zz_terms": zz_terms,
        "num_z_terms": len(rounded_z_terms),
        "num_zz_terms": len(zz_terms),
    }


def calculate_qubo_energy(solution: dict, linear_terms: dict, quadratic_terms: list) -> float:
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


def exact_solve_small_vqe_problem(problem: dict) -> dict:
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

        energy = calculate_qubo_energy(solution, linear_terms, quadratic_terms)

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
        "solver": "exact search on VQE-ready subset",
        "variable_count": len(variables),
        "best_energy": best_energy,
        "best_solution": best_solution,
        "selected_variables": selected_variables,
        "selected_variable_count": len(selected_variables),
    }


def run_vqe_readiness_demo(sequence: str, max_variables: int = 10) -> dict:
    problem = build_small_vqe_problem(sequence, max_variables=max_variables)
    hamiltonian = qubo_to_ising_terms(problem)
    exact_result = exact_solve_small_vqe_problem(problem)

    return {
        "success": True,
        "phase": "Phase 17 — VQE readiness prototype",
        "problem": problem,
        "hamiltonian": hamiltonian,
        "exact_subset_baseline": exact_result,
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_vqe_readiness_demo(sequence)

    print("VQE readiness prototype summary")
    print("-------------------------------")
    print(f"success: {result['success']}")
    print(f"phase: {result['phase']}")
    print(f"original_qubo_variables: {result['problem']['original_qubo_variables']}")
    print(f"selected_variable_count: {result['problem']['selected_variable_count']}")
    print(f"estimated_vqe_qubits: {result['problem']['estimated_vqe_qubits']}")
    print(f"num_z_terms: {result['hamiltonian']['num_z_terms']}")
    print(f"num_zz_terms: {result['hamiltonian']['num_zz_terms']}")
    print(f"best_energy: {result['exact_subset_baseline']['best_energy']}")
    print(f"selected_variables: {result['exact_subset_baseline']['selected_variables']}")