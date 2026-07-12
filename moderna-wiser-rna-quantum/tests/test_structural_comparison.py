from __future__ import annotations

import math
import pytest
from src.evaluation.structural_comparison import compare_structures


def test_perfect_match_gives_f1_one():
    result = compare_structures("((...))", "((...))")
    assert math.isclose(result["f1_score"], 1.0)
    assert result["base_pair_distance"] == 0


def test_no_predicted_pairs_gives_f1_zero():
    result = compare_structures("((...))", ".......")
    assert math.isclose(result["f1_score"], 0.0)
    assert result["false_negatives"] == 2


def test_partial_overlap_calculates_metrics():
    result = compare_structures("((...))", "(.....)")
    assert result["true_positives"] == 1
    assert math.isclose(result["f1_score"], 2 / 3)


def test_length_mismatch_raises_error():
    with pytest.raises(ValueError):
        compare_structures("((...))", "......")
