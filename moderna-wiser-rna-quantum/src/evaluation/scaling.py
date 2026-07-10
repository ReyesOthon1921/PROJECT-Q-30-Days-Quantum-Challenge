"""
scaling.py

Phase 9 scaling analysis.

This module runs the RNA pipeline across multiple sequence lengths and records:
- candidate pair count
- candidate stem count
- QUBO variables
- QUBO quadratic penalties
- greedy solver output
- ViennaRNA runtime
- precision / recall / F1
"""

import csv
import time
from pathlib import Path

from src.classical.sequence_tools import clean_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark
from src.qubo.candidate_pairs import summarize_candidate_pairs
from src.qubo.candidate_stems import summarize_candidate_stems
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.evaluation.metrics import evaluate_greedy_against_vienna


DEFAULT_BASE_SEQUENCE = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"


def synthetic_sequence(length: int) -> str:
    """
    Create a simple synthetic RNA sequence of a target length.
    """
    pattern = "GGCAUUAACGCU"
    repeated = pattern * ((length // len(pattern)) + 1)
    return repeated[:length]


def run_scaling_experiment(lengths=None) -> list:
    """
    Run pipeline scaling for several RNA sequence lengths.
    """
    if lengths is None:
        lengths = [12, 16, 20, 24, 28, 32, 36, 40, 44]

    records = []

    for length in lengths:
        sequence = synthetic_sequence(length)
        cleaned = clean_sequence(sequence)

        start_total = time.perf_counter()

        pair_summary = summarize_candidate_pairs(cleaned)
        stem_summary = summarize_candidate_stems(cleaned)
        qubo = build_stem_qubo(cleaned)
        greedy = solve_stem_qubo_greedy(cleaned)
        vienna = run_vienna_benchmark(cleaned)
        evaluation = evaluate_greedy_against_vienna(cleaned)

        total_runtime = round(time.perf_counter() - start_total, 6)

        metrics = evaluation.get("metrics", {}) if evaluation.get("success") else {}

        records.append(
            {
                "sequence_length": length,
                "candidate_pair_count": pair_summary["candidate_pair_count"],
                "candidate_stem_count": stem_summary["candidate_stem_count"],
                "qubo_variables": qubo["num_variables"],
                "estimated_qubits": qubo["estimated_qubits"],
                "qubo_quadratic_terms": qubo["num_quadratic_terms"],
                "greedy_selected_stems": greedy["selected_stem_count"],
                "greedy_selected_pairs": greedy["selected_pair_count"],
                "greedy_objective_score": greedy["objective_score"],
                "vienna_available": vienna.get("vienna_available", False),
                "vienna_mfe_energy": vienna.get("mfe_energy", None),
                "vienna_runtime_seconds": vienna.get("runtime_seconds", None),
                "precision": metrics.get("precision", None),
                "recall": metrics.get("recall", None),
                "f1_score": metrics.get("f1_score", None),
                "total_runtime_seconds": total_runtime,
            }
        )

    return records


def save_scaling_results(records: list, output_path: str = "results/scaling_results.csv") -> str:
    """
    Save scaling results as CSV.
    """
    Path("results").mkdir(exist_ok=True)

    fieldnames = [
        "sequence_length",
        "candidate_pair_count",
        "candidate_stem_count",
        "qubo_variables",
        "estimated_qubits",
        "qubo_quadratic_terms",
        "greedy_selected_stems",
        "greedy_selected_pairs",
        "greedy_objective_score",
        "vienna_available",
        "vienna_mfe_energy",
        "vienna_runtime_seconds",
        "precision",
        "recall",
        "f1_score",
        "total_runtime_seconds",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    return output_path


def run_and_save_scaling_experiment() -> dict:
    records = run_scaling_experiment()
    output_path = save_scaling_results(records)

    return {
        "success": True,
        "output_path": output_path,
        "num_records": len(records),
        "records": records,
    }


if __name__ == "__main__":
    result = run_and_save_scaling_experiment()

    print("Scaling experiment summary")
    print("--------------------------")
    print(f"success: {result['success']}")
    print(f"output_path: {result['output_path']}")
    print(f"num_records: {result['num_records']}")

    for record in result["records"]:
        print(record)