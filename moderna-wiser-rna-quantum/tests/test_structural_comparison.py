import pytest

from src.evaluation.structural_comparison import compare_structures


def test_perfect_match_gives_f1_one() -> None:
    metrics = compare_structures("((...))", "((...))")
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1_score"] == 1.0
    assert metrics["exact_match"] is True


def test_no_predicted_pairs_gives_f1_zero() -> None:
    metrics = compare_structures("((...))", ".......")
    assert metrics["f1_score"] == 0.0
    assert metrics["false_negatives"] == 2


def test_partial_overlap_metrics() -> None:
    metrics = compare_structures("((...))", "(.....)")
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 0.5
    assert metrics["f1_score"] == pytest.approx(2.0 / 3.0, abs=1e-6)
