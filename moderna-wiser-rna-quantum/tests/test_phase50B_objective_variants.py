from __future__ import annotations

from src.qubo.objective_variants import (
    build_variant_qubo,
    score_stem_variant,
    solve_variant_qubo_greedy,
)


def test_baseline_sum_matches_original_pair_rewards():
    stem = {"length": 3, "pair_types": ["G-C", "A-U", "G-U wobble"]}
    score = score_stem_variant(stem, {"reward_mode": "sum"})
    assert score == -6.0


def test_short_stem_penalty_applies_only_to_target_length():
    short = {"length": 2, "pair_types": ["G-C", "C-G"]}
    long = {"length": 3, "pair_types": ["G-C", "C-G", "G-C"]}
    settings = {"reward_mode": "sum", "short_stem_penalty": 2.0, "short_stem_length": 2}
    assert score_stem_variant(short, settings) == -4.0
    assert score_stem_variant(long, settings) == -9.0


def test_mean_and_sqrt_modes_are_sublinear():
    stem = {"length": 4, "pair_types": ["G-C"] * 4}
    assert score_stem_variant(stem, {"reward_mode": "mean_pair"}) == -3.0
    assert score_stem_variant(stem, {"reward_mode": "sqrt_length"}) == -6.0


def test_min_stem_length_variant_reduces_candidate_space():
    strict = {"stem_min_length": 2, "min_loop_length": 3, "allow_wobble": True,
              "overlap_penalty": 14.0, "crossing_penalty": 12.0}
    sequence = "GCAAAAGC"
    baseline = build_variant_qubo(sequence, strict, {"reward_mode": "sum", "min_stem_length": 2})
    stricter = build_variant_qubo(sequence, strict, {"reward_mode": "sum", "min_stem_length": 3})
    assert baseline["num_variables"] >= 1
    assert stricter["num_variables"] == 0


def test_greedy_skips_positive_linear_stem():
    strict = {"stem_min_length": 2, "min_loop_length": 3, "allow_wobble": True,
              "overlap_penalty": 14.0, "crossing_penalty": 12.0}
    qubo = build_variant_qubo(
        "GCAAAAGC",
        strict,
        {"reward_mode": "sum", "short_stem_penalty": 10.0, "short_stem_length": 2},
    )
    result = solve_variant_qubo_greedy("GCAAAAGC", qubo)
    assert result["selected_stem_count"] == 0
    assert result["best_energy"] == 0.0
    assert result["predicted_structure"] == "........"


def test_exact_solver_reports_degenerate_optimal_structures():
    from src.qubo.objective_variants import solve_variant_qubo_exact

    qubo = {
        "linear_terms": {"s_0": -1.0, "s_1": 0.0},
        "quadratic_terms": [],
        "stems": [
            {
                "stem_index": 0,
                "variable_name": "s_0",
                "length": 2,
                "pairs": [(0, 9), (1, 8)],
                "pair_types": ["G-C", "C-G"],
            },
            {
                "stem_index": 1,
                "variable_name": "s_1",
                "length": 2,
                "pairs": [(2, 7), (3, 6)],
                "pair_types": ["G-C", "C-G"],
            },
        ],
    }
    result = solve_variant_qubo_exact(
        "GGGGAACCCC",
        qubo,
        max_variables=20,
        collect_optimal_structures=True,
    )
    assert result["status"] == "success"
    assert result["best_energy"] == -1.0
    assert result["optimal_assignment_count"] == 2
    assert result["captured_optimal_structure_count"] == 2
    assert result["optimal_structures_truncated"] is False
