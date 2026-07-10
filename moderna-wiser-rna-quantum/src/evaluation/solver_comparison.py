"""
solver_comparison.py

Phase 12 solver comparison layer.

Compares:
1. ViennaRNA benchmark
2. Greedy stem-QUBO baseline
3. Simulated annealing stem-QUBO baseline
"""

from typing import Optional

from src.classical.sequence_tools import clean_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import solve_stem_qubo_simulated_annealing
from src.evaluation.metrics import precision_recall_f1


def evaluate_solver_structure(
    solver_name: str,
    predicted_structure: Optional[str],
    reference_structure: str,
    extra_fields: Optional[dict] = None,
) -> dict:
    """
    Compare one solver's predicted dot-bracket structure against ViennaRNA.
    """
    if extra_fields is None:
        extra_fields = {}

    if not predicted_structure:
        return {
            "solver": solver_name,
            "can_evaluate": False,
            "error": "Solver did not return a valid predicted dot-bracket structure.",
            **extra_fields,
        }

    metrics = precision_recall_f1(
        predicted_structure=predicted_structure,
        reference_structure=reference_structure,
    )

    return {
        "solver": solver_name,
        "can_evaluate": True,
        "predicted_structure": predicted_structure,
        "metrics": metrics,
        **extra_fields,
    }


def compare_solvers(sequence: str) -> dict:
    """
    Compare greedy and simulated annealing solvers against ViennaRNA.
    """
    cleaned = clean_sequence(sequence)

    vienna_result = run_vienna_benchmark(cleaned)

    if not vienna_result.get("success"):
        return {
            "success": False,
            "error": "ViennaRNA benchmark could not run.",
            "vienna_result": vienna_result,
        }

    reference_structure = vienna_result["structure"]

    greedy_result = solve_stem_qubo_greedy(cleaned)
    annealing_result = solve_stem_qubo_simulated_annealing(cleaned)

    greedy_eval = evaluate_solver_structure(
        solver_name="greedy stem-QUBO baseline",
        predicted_structure=greedy_result.get("predicted_structure"),
        reference_structure=reference_structure,
        extra_fields={
            "objective_score": greedy_result.get("objective_score"),
            "selected_stem_count": greedy_result.get("selected_stem_count"),
            "selected_pair_count": greedy_result.get("selected_pair_count"),
        },
    )

    annealing_eval = evaluate_solver_structure(
        solver_name="simulated annealing stem-QUBO baseline",
        predicted_structure=annealing_result.get("predicted_structure"),
        reference_structure=reference_structure,
        extra_fields={
            "best_energy": annealing_result.get("best_energy"),
            "selected_stem_count": annealing_result.get("selected_stem_count"),
            "selected_pair_count": annealing_result.get("selected_pair_count"),
            "is_conflict_free": annealing_result.get("is_conflict_free"),
            "runtime_seconds": annealing_result.get("runtime_seconds"),
            "structure_error": annealing_result.get("structure_error"),
        },
    )

    comparison_rows = []

    for result in [greedy_eval, annealing_eval]:
        if result.get("can_evaluate"):
            comparison_rows.append(
                {
                    "solver": result["solver"],
                    "precision": result["metrics"]["precision"],
                    "recall": result["metrics"]["recall"],
                    "f1_score": result["metrics"]["f1_score"],
                    "selected_stem_count": result.get("selected_stem_count"),
                    "selected_pair_count": result.get("selected_pair_count"),
                }
            )
        else:
            comparison_rows.append(
                {
                    "solver": result["solver"],
                    "precision": None,
                    "recall": None,
                    "f1_score": None,
                    "selected_stem_count": result.get("selected_stem_count"),
                    "selected_pair_count": result.get("selected_pair_count"),
                    "error": result.get("error"),
                }
            )

    valid_rows = [
        row for row in comparison_rows
        if row["f1_score"] is not None
    ]

    best_solver = None

    if valid_rows:
        best_solver = max(
            valid_rows,
            key=lambda row: (
                row["f1_score"],
                row["precision"],
                row["recall"],
            ),
        )

    return {
        "success": True,
        "sequence": cleaned,
        "length": len(cleaned),
        "reference_method": "ViennaRNA RNA.fold",
        "vienna_structure": reference_structure,
        "vienna_mfe_energy": vienna_result["mfe_energy"],
        "vienna_runtime_seconds": vienna_result["runtime_seconds"],
        "score_note": "ViennaRNA MFE, greedy objective score, and annealing best energy are not identical units.",
        "comparison_rows": comparison_rows,
        "best_solver_by_f1": best_solver,
        "greedy_evaluation": greedy_eval,
        "annealing_evaluation": annealing_eval,
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = compare_solvers(sequence)

    print("Solver comparison summary")
    print("-------------------------")
    print(f"success: {result['success']}")
    print(f"sequence: {result['sequence']}")
    print(f"length: {result['length']}")
    print(f"vienna_structure: {result['vienna_structure']}")
    print(f"vienna_mfe_energy: {result['vienna_mfe_energy']}")
    print(f"comparison_rows: {result['comparison_rows']}")
    print(f"best_solver_by_f1: {result['best_solver_by_f1']}")