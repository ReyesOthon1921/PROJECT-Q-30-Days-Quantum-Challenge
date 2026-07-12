"""Base-pair-level structural comparison for the strict classical pipeline."""

from __future__ import annotations

from typing import Any

from src.classical.dotbracket_tools import dotbracket_to_pairs


def compare_structures(
    reference_dotbracket: str,
    predicted_dotbracket: str,
) -> dict[str, Any]:
    """Compare two equal-length structures using 0-based base-pair sets."""

    if len(reference_dotbracket) != len(predicted_dotbracket):
        raise ValueError(
            "Reference and predicted structures must have equal lengths: "
            f"{len(reference_dotbracket)} != {len(predicted_dotbracket)}"
        )

    reference_pairs = set(dotbracket_to_pairs(reference_dotbracket))
    predicted_pairs = set(dotbracket_to_pairs(predicted_dotbracket))

    true_positive_pairs = reference_pairs & predicted_pairs
    false_positive_pairs = predicted_pairs - reference_pairs
    false_negative_pairs = reference_pairs - predicted_pairs

    if not reference_pairs and not predicted_pairs:
        precision = recall = f1_score = 1.0
    else:
        precision = (
            len(true_positive_pairs) / len(predicted_pairs)
            if predicted_pairs
            else 0.0
        )
        recall = (
            len(true_positive_pairs) / len(reference_pairs)
            if reference_pairs
            else 0.0
        )
        f1_score = (
            2.0 * precision * recall / (precision + recall)
            if precision + recall > 0.0
            else 0.0
        )

    return {
        "reference_pair_count": len(reference_pairs),
        "predicted_pair_count": len(predicted_pairs),
        "true_positives": len(true_positive_pairs),
        "false_positives": len(false_positive_pairs),
        "false_negatives": len(false_negative_pairs),
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1_score": round(f1_score, 6),
        "exact_match": reference_dotbracket == predicted_dotbracket,
        "base_pair_distance": len(false_positive_pairs) + len(false_negative_pairs),
        "true_positive_pairs": sorted(true_positive_pairs),
        "false_positive_pairs": sorted(false_positive_pairs),
        "false_negative_pairs": sorted(false_negative_pairs),
    }
