"""
metrics.py

Phase 8 evaluation metrics.

This module compares a predicted RNA secondary structure against
a ViennaRNA benchmark structure using base-pair precision, recall, and F1.
"""

from src.classical.dotbracket import dotbracket_to_pairs
from src.classical.sequence_tools import clean_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark
from src.solvers.greedy_solver import solve_stem_qubo_greedy


def base_pair_set(structure: str) -> set:
    """
    Convert dot-bracket structure to a set of base-pair tuples.
    """
    return set(dotbracket_to_pairs(structure))


def precision_recall_f1(predicted_structure: str, reference_structure: str) -> dict:
    """
    Compare predicted base pairs to reference base pairs.
    """
    predicted_pairs = base_pair_set(predicted_structure)
    reference_pairs = base_pair_set(reference_structure)

    true_positives = predicted_pairs & reference_pairs
    false_positives = predicted_pairs - reference_pairs
    false_negatives = reference_pairs - predicted_pairs

    precision = 0.0
    recall = 0.0
    f1_score = 0.0

    if len(predicted_pairs) > 0:
        precision = len(true_positives) / len(predicted_pairs)

    if len(reference_pairs) > 0:
        recall = len(true_positives) / len(reference_pairs)

    if precision + recall > 0:
        f1_score = 2 * precision * recall / (precision + recall)

    return {
        "predicted_pair_count": len(predicted_pairs),
        "reference_pair_count": len(reference_pairs),
        "true_positive_count": len(true_positives),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "true_positives": sorted(true_positives),
        "false_positives": sorted(false_positives),
        "false_negatives": sorted(false_negatives),
    }


def evaluate_greedy_against_vienna(sequence: str) -> dict:
    """
    Run ViennaRNA and the greedy QUBO solver, then compare structures.
    """
    cleaned = clean_sequence(sequence)

    vienna_result = run_vienna_benchmark(cleaned)

    if not vienna_result.get("success"):
        return {
            "success": False,
            "error": "ViennaRNA benchmark could not run.",
            "vienna_result": vienna_result,
        }

    greedy_result = solve_stem_qubo_greedy(cleaned)

    vienna_structure = vienna_result["structure"]
    greedy_structure = greedy_result["predicted_structure"]

    metrics = precision_recall_f1(
        predicted_structure=greedy_structure,
        reference_structure=vienna_structure,
    )

    return {
        "success": True,
        "sequence": cleaned,
        "length": len(cleaned),
        "reference_method": "ViennaRNA RNA.fold",
        "candidate_method": "greedy stem-QUBO baseline",
        "vienna_structure": vienna_structure,
        "greedy_structure": greedy_structure,
        "vienna_mfe_energy": vienna_result["mfe_energy"],
        "greedy_objective_score": greedy_result["objective_score"],
        "score_note": "ViennaRNA MFE energy and greedy QUBO objective score are not the same unit.",
        "metrics": metrics,
        "vienna_runtime_seconds": vienna_result["runtime_seconds"],
        "greedy_selected_stem_count": greedy_result["selected_stem_count"],
        "greedy_selected_pair_count": greedy_result["selected_pair_count"],
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = evaluate_greedy_against_vienna(sequence)

    print("Evaluation summary")
    print("------------------")
    print(f"success: {result['success']}")
    print(f"sequence: {result['sequence']}")
    print(f"length: {result['length']}")
    print(f"vienna_structure: {result['vienna_structure']}")
    print(f"greedy_structure: {result['greedy_structure']}")
    print(f"vienna_mfe_energy: {result['vienna_mfe_energy']}")
    print(f"greedy_objective_score: {result['greedy_objective_score']}")
    print(f"precision: {result['metrics']['precision']}")
    print(f"recall: {result['metrics']['recall']}")
    print(f"f1_score: {result['metrics']['f1_score']}")
    print(f"true_positive_count: {result['metrics']['true_positive_count']}")
    print(f"false_positive_count: {result['metrics']['false_positive_count']}")
    print(f"false_negative_count: {result['metrics']['false_negative_count']}")