"""Aggregate metrics and scaling summaries for Phase 49 RNA benchmarks."""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any, Iterable


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _mean(values: Iterable[float]) -> float | None:
    collected = list(values)
    return round(statistics.fmean(collected), 6) if collected else None


def _median(values: Iterable[float]) -> float | None:
    collected = list(values)
    return round(statistics.median(collected), 6) if collected else None


def _percentile(values: Iterable[float], probability: float) -> float | None:
    collected = sorted(values)
    if not collected:
        return None
    if len(collected) == 1:
        return round(collected[0], 6)
    position = (len(collected) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return round(collected[lower], 6)
    weight = position - lower
    return round(
        collected[lower] * (1.0 - weight) + collected[upper] * weight,
        6,
    )


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def summarize_benchmark_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate accuracy, solver-agreement, and runtime metrics.

    Rows marked unsuccessful or missing a structural comparison are excluded from
    structural aggregates but remain visible in total/success counts.
    """

    total = len(rows)
    successful = [row for row in rows if _as_bool(row.get("success"))]
    comparable = [
        row
        for row in successful
        if row.get("f1_score") not in (None, "")
        and row.get("base_pair_distance") not in (None, "")
    ]

    tp = sum(_as_int(row.get("true_positives")) for row in comparable)
    fp = sum(_as_int(row.get("false_positives")) for row in comparable)
    fn = sum(_as_int(row.get("false_negatives")) for row in comparable)

    if tp == 0 and fp == 0 and fn == 0 and comparable:
        micro_precision = micro_recall = micro_f1 = 1.0
    else:
        micro_precision = tp / (tp + fp) if tp + fp else 0.0
        micro_recall = tp / (tp + fn) if tp + fn else 0.0
        micro_f1 = _f1(micro_precision, micro_recall)

    nontrivial = [
        row for row in comparable if _as_int(row.get("reference_pair_count")) > 0
    ]
    empty_reference = [
        row for row in comparable if _as_int(row.get("reference_pair_count")) == 0
    ]

    runtime_values = [
        _as_float(row.get("total_runtime_seconds"))
        for row in successful
        if row.get("total_runtime_seconds") not in (None, "")
    ]
    qvar_values = [
        _as_float(row.get("qubo_variable_count"))
        for row in successful
        if row.get("qubo_variable_count") not in (None, "")
    ]

    agreement_eligible = [
        row
        for row in successful
        if _as_int(row.get("successful_solver_count")) >= 2
    ]

    summary = {
        "sequence_count": total,
        "successful_sequence_count": len(successful),
        "failed_sequence_count": total - len(successful),
        "success_rate": round(len(successful) / total, 6) if total else 0.0,
        "comparable_sequence_count": len(comparable),
        "nontrivial_reference_count": len(nontrivial),
        "empty_reference_count": len(empty_reference),
        "micro_true_positives": tp,
        "micro_false_positives": fp,
        "micro_false_negatives": fn,
        "micro_precision": round(micro_precision, 6),
        "micro_recall": round(micro_recall, 6),
        "micro_f1": round(micro_f1, 6),
        "macro_precision_all": _mean(
            _as_float(row.get("precision")) for row in comparable
        ),
        "macro_recall_all": _mean(
            _as_float(row.get("recall")) for row in comparable
        ),
        "macro_f1_all": _mean(
            _as_float(row.get("f1_score")) for row in comparable
        ),
        "macro_f1_nontrivial_reference": _mean(
            _as_float(row.get("f1_score")) for row in nontrivial
        ),
        "exact_match_rate": _mean(
            1.0 if _as_bool(row.get("exact_match")) else 0.0
            for row in comparable
        ),
        "empty_structure_accuracy": _mean(
            1.0 if _as_int(row.get("predicted_pair_count")) == 0 else 0.0
            for row in empty_reference
        ),
        "mean_base_pair_distance": _mean(
            _as_float(row.get("base_pair_distance")) for row in comparable
        ),
        "median_base_pair_distance": _median(
            _as_float(row.get("base_pair_distance")) for row in comparable
        ),
        "mean_normalized_base_pair_distance": _mean(
            _as_float(row.get("normalized_base_pair_distance"))
            for row in comparable
        ),
        "solver_agreement_eligible_count": len(agreement_eligible),
        "solver_structure_agreement_rate": _mean(
            1.0 if _as_bool(row.get("solver_structure_agreement")) else 0.0
            for row in agreement_eligible
        ),
        "solver_energy_agreement_rate": _mean(
            1.0 if _as_bool(row.get("solver_energy_agreement")) else 0.0
            for row in agreement_eligible
        ),
        "mean_total_runtime_seconds": _mean(runtime_values),
        "median_total_runtime_seconds": _median(runtime_values),
        "p95_total_runtime_seconds": _percentile(runtime_values, 0.95),
        "mean_qubo_variable_count": _mean(qvar_values),
        "max_qubo_variable_count": max(qvar_values) if qvar_values else None,
    }
    return summary


def summarize_groups(
    rows: list[dict[str, Any]],
    field: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(field, "unknown"))].append(row)

    summaries = []
    for value in sorted(grouped):
        summary = summarize_benchmark_rows(grouped[value])
        summary[field] = value
        summaries.append(summary)
    return summaries


def length_bucket(length: int) -> str:
    if length <= 16:
        return "01_12-16"
    if length <= 24:
        return "02_17-24"
    if length <= 32:
        return "03_25-32"
    if length <= 48:
        return "04_33-48"
    return "05_49_plus"


def linear_regression(x_values: list[float], y_values: list[float]) -> dict[str, Any]:
    """Return a simple least-squares line, R², and Pearson correlation."""

    pairs = [
        (float(x), float(y))
        for x, y in zip(x_values, y_values)
        if math.isfinite(float(x)) and math.isfinite(float(y))
    ]
    if len(pairs) < 2:
        return {
            "n": len(pairs),
            "slope": None,
            "intercept": None,
            "r_squared": None,
            "pearson_r": None,
        }

    xs = [pair[0] for pair in pairs]
    ys = [pair[1] for pair in pairs]
    mean_x = statistics.fmean(xs)
    mean_y = statistics.fmean(ys)
    ss_x = sum((x - mean_x) ** 2 for x in xs)
    ss_y = sum((y - mean_y) ** 2 for y in ys)
    covariance = sum((x - mean_x) * (y - mean_y) for x, y in pairs)

    if ss_x == 0.0:
        slope = 0.0
        intercept = mean_y
        predictions = [mean_y for _ in xs]
    else:
        slope = covariance / ss_x
        intercept = mean_y - slope * mean_x
        predictions = [intercept + slope * x for x in xs]

    residual_ss = sum((y - predicted) ** 2 for y, predicted in zip(ys, predictions))
    r_squared = 1.0 - residual_ss / ss_y if ss_y > 0.0 else 1.0
    pearson_r = covariance / math.sqrt(ss_x * ss_y) if ss_x > 0.0 and ss_y > 0.0 else 0.0

    return {
        "n": len(pairs),
        "slope": round(slope, 9),
        "intercept": round(intercept, 9),
        "r_squared": round(r_squared, 6),
        "pearson_r": round(pearson_r, 6),
    }


def summarize_scaling(rows: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [row for row in rows if _as_bool(row.get("success"))]

    def values(x_key: str, y_key: str) -> tuple[list[float], list[float]]:
        pairs = [
            (_as_float(row.get(x_key)), _as_float(row.get(y_key)))
            for row in successful
            if row.get(x_key) not in (None, "")
            and row.get(y_key) not in (None, "")
        ]
        return [pair[0] for pair in pairs], [pair[1] for pair in pairs]

    relationships = {}
    for name, x_key, y_key in (
        ("length_to_candidate_pairs", "sequence_length", "candidate_pair_count"),
        ("length_to_qubo_variables", "sequence_length", "qubo_variable_count"),
        ("length_to_quadratic_terms", "sequence_length", "quadratic_term_count"),
        ("length_to_runtime", "sequence_length", "total_runtime_seconds"),
        ("qubo_variables_to_runtime", "qubo_variable_count", "total_runtime_seconds"),
        ("qubo_variables_to_quadratic_terms", "qubo_variable_count", "quadratic_term_count"),
    ):
        xs, ys = values(x_key, y_key)
        relationships[name] = linear_regression(xs, ys)

    return {
        "successful_sequence_count": len(successful),
        "relationships": relationships,
        "warning": (
            "These regressions describe this benchmark range only. They are not "
            "proof of asymptotic complexity or quantum advantage."
        ),
    }
