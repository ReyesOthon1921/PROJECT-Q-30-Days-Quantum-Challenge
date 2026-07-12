"""Base-pair-level structural comparison for the strict classical pipeline."""

from __future__ import annotations

from typing import Dict

from src.classical.dotbracket_tools import dotbracket_to_pairs


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0

    return numerator / denominator


def compare_structures(
    reference_dotbracket: str,
    predicted_dotbracket: str,
) -> Dict[str, object]:
    if len(reference_dotbracket) != len(predicted_dotbracket):
        raise ValueError(
            "Reference and predicted structures must have the same length. "
            f"Reference length={len(reference_dotbracket)}, "
            f"predicted length={len(predicted_dotbracket)}."
        )

    reference_pairs = set(dotbracket_to_pairs(reference_dotbracket))
    predicted_pairs = set(dotbracket_to_pairs(predicted_dotbracket))

    true_positives = len(reference_pairs.intersection(predicted_pairs))
    false_positives = len(predicted_pairs - reference_pairs)
    false_negatives = len(reference_pairs - predicted_pairs)

    precision = safe_divide(true_positives, true_positives + false_positives)
    recall = safe_divide(true_positives, true_positives + false_negatives)

    if precision + recall == 0:
        f1_score = 0.0
    else:
        f1_score = 2 * precision * recall / (precision + recall)

    base_pair_distance = false_positives + false_negatives

    return {
        "reference_dotbracket": reference_dotbracket,
        "predicted_dotbracket": predicted_dotbracket,
        "reference_pair_count": len(reference_pairs),
        "predicted_pair_count": len(predicted_pairs),
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "exact_match": reference_dotbracket == predicted_dotbracket,
        "base_pair_distance": base_pair_distance,
        "reference_pairs": sorted(reference_pairs),
        "predicted_pairs": sorted(predicted_pairs),
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Compare a predicted RNA dot-bracket structure against a reference."
    )
    parser.add_argument("--reference", required=True)
    parser.add_argument("--predicted", required=True)

    args = parser.parse_args()

    result = compare_structures(
        reference_dotbracket=args.reference,
        predicted_dotbracket=args.predicted,
    )

    print(json.dumps(result, indent=2))