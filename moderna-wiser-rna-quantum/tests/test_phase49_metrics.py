from src.evaluation.phase49_metrics import (
    length_bucket,
    linear_regression,
    summarize_benchmark_rows,
    summarize_scaling,
)


def test_aggregate_metrics_include_micro_macro_and_empty_controls():
    rows = [
        {
            "success": True,
            "true_positives": 2,
            "false_positives": 1,
            "false_negatives": 1,
            "precision": 2 / 3,
            "recall": 2 / 3,
            "f1_score": 2 / 3,
            "exact_match": False,
            "base_pair_distance": 2,
            "normalized_base_pair_distance": 0.1,
            "reference_pair_count": 3,
            "predicted_pair_count": 3,
            "successful_solver_count": 3,
            "solver_structure_agreement": True,
            "solver_energy_agreement": True,
            "total_runtime_seconds": 0.2,
            "qubo_variable_count": 4,
        },
        {
            "success": True,
            "true_positives": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "precision": 1.0,
            "recall": 1.0,
            "f1_score": 1.0,
            "exact_match": True,
            "base_pair_distance": 0,
            "normalized_base_pair_distance": 0.0,
            "reference_pair_count": 0,
            "predicted_pair_count": 0,
            "successful_solver_count": 2,
            "solver_structure_agreement": True,
            "solver_energy_agreement": True,
            "total_runtime_seconds": 0.1,
            "qubo_variable_count": 0,
        },
    ]
    summary = summarize_benchmark_rows(rows)
    assert summary["sequence_count"] == 2
    assert summary["micro_f1"] == 0.666667
    assert summary["macro_f1_nontrivial_reference"] == 0.666667
    assert summary["empty_structure_accuracy"] == 1.0
    assert summary["solver_structure_agreement_rate"] == 1.0


def test_length_bucket_boundaries():
    assert length_bucket(12) == "01_12-16"
    assert length_bucket(24) == "02_17-24"
    assert length_bucket(32) == "03_25-32"
    assert length_bucket(48) == "04_33-48"
    assert length_bucket(49) == "05_49_plus"


def test_linear_regression_detects_exact_line():
    result = linear_regression([1, 2, 3], [2, 4, 6])
    assert result["slope"] == 2.0
    assert result["intercept"] == 0.0
    assert result["r_squared"] == 1.0
    assert result["pearson_r"] == 1.0


def test_scaling_summary_has_expected_relationships():
    rows = [
        {
            "success": True,
            "sequence_length": 10,
            "candidate_pair_count": 2,
            "qubo_variable_count": 1,
            "quadratic_term_count": 0,
            "total_runtime_seconds": 0.1,
        },
        {
            "success": True,
            "sequence_length": 20,
            "candidate_pair_count": 6,
            "qubo_variable_count": 3,
            "quadratic_term_count": 2,
            "total_runtime_seconds": 0.2,
        },
    ]
    summary = summarize_scaling(rows)
    assert summary["successful_sequence_count"] == 2
    assert "length_to_qubo_variables" in summary["relationships"]
    assert summary["relationships"]["length_to_qubo_variables"]["n"] == 2
