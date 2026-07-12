from __future__ import annotations

import math

import pytest

from src.evaluation.structural_comparison import compare_structures


def test_perfect_match_gives_f1_one():
    result = compare_structures("((...))", "((...))")

    assert result["true_positives"] == 2
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert math.isclose(result["precision"], 1.0)
    assert math.isclose(result["recall"], 1.0)
    assert math.isclose(result["f1_score"], 1.0)
    assert result["exact_match"] is True
    assert result["base_pair_distance"] == 0


def test_no_predicted_pairs_gives_f1_zero():
    result = compare_structures("((...))", ".......")

    assert result["reference_pair_count"] == 2
    assert result["predicted_pair_count"] == 0
    assert result["true_positives"] == 0
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 2
    assert math.isclose(result["precision"], 0.0)
    assert math.isclose(result["recall"], 0.0)
    assert math.isclose(result["f1_score"], 0.0)
    assert result["exact_match"] is False
    assert result["base_pair_distance"] == 2


def test_partial_overlap_calculates_metrics():
    result = compare_structures("((...))", "(.....)")

    assert result["reference_pair_count"] == 2
    assert result["predicted_pair_count"] == 1
    assert result["true_positives"] == 1
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 1
    assert math.isclose(result["precision"], 1.0)
    assert math.isclose(result["recall"], 0.5)
    assert math.isclose(result["f1_score"], 2 / 3)
    assert result["base_pair_distance"] == 1


def test_length_mismatch_raises_error():
    with pytest.raises(ValueError):
        compare_structures("((...))", "......")