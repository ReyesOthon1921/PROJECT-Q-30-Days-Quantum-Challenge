from __future__ import annotations

from pathlib import Path

import pytest
import yaml

import src.evaluation.phase50B_equal_budget_audit as audit


def _summary(variant_id: str, exact_failure_rate: float) -> dict:
    return {
        "variant_id": variant_id,
        "success_rate": 1.0,
        "controls_preserved": True,
        "mixed_mean_best_known_f1": 0.5,
        "dev_mixed_18_f1": 0.5,
        "micro_f1": 0.5,
        "exact_strict_failure_rate": exact_failure_rate,
        "exact_ambiguity_count": 0,
        "false_positives": 2,
        "false_negatives": 2,
        "mean_sa_best_energy_hit_rate": 0.5,
        "mean_sa_unique_structure_count": 3.0,
        "mean_qubo_variable_count": 10.0,
        "mean_runtime_seconds": 1.0,
    }


def test_equal_budget_ranking_uses_exact_failure_guardrail():
    better = _summary("better", 0.0)
    worse = _summary("worse", 0.5)
    assert audit.ranking_key(better) < audit.ranking_key(worse)


def test_development_loader_blocks_final_test(tmp_path: Path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,split,category,source_type,sequence,notes\n"
        "dev_a,development,unstructured_control,synthetic,AAAAAAAA,dev\n"
        "final_a,final_test,unstructured_control,synthetic,UUUUUUUU,final\n",
        encoding="utf-8",
    )
    rows = audit.load_development_dataset(dataset)
    assert [row["sequence_id"] for row in rows] == ["dev_a"]


def test_equal_budget_smoke_and_signature_guard(tmp_path: Path, monkeypatch):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,split,category,source_type,sequence,notes\n"
        "dev_a,development,unstructured_control,synthetic,AAAAAAAA,dev\n"
        "final_a,final_test,unstructured_control,synthetic,UUUUUUUU,final\n",
        encoding="utf-8",
    )
    strict = tmp_path / "strict.yaml"
    strict.write_text(
        "stem_min_length: 2\nmin_loop_length: 3\nallow_wobble: true\n"
        "overlap_penalty: 14.0\ncrossing_penalty: 12.0\n"
        "rnafold_executable: RNAfold\nallow_vienna_python_fallback: true\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "results"
    config_path = tmp_path / "audit.yaml"
    config = {
        "dataset_path": str(dataset),
        "strict_config_path": str(strict),
        "output_root": str(output_root),
        "resume": True,
        "exact_max_variables": 20,
        "optimal_structure_capture_limit": 32,
        "budget": {
            "sa_seeds": [3],
            "sa_steps": 5,
            "sa_initial_temperature": 1.0,
            "sa_final_temperature": 0.01,
            "sa_cooling_rate": 0.9,
            "run_local_refinement": True,
        },
        "selection": {
            "baseline_variant_id": "baseline_sum",
            "micro_f1_noninferiority_margin": 0.03,
            "exact_failure_rate_noninferiority_margin": 0.0,
        },
        "variants": [
            {
                "id": "baseline_sum",
                "description": "baseline",
                "objective": {"reward_mode": "sum", "short_stem_penalty": 0.0, "min_stem_length": 2},
            },
            {
                "id": "short2_penalty_3",
                "description": "penalty",
                "objective": {"reward_mode": "sum", "short_stem_penalty": 3.0, "short_stem_length": 2, "min_stem_length": 2},
            },
            {
                "id": "min_stem_length_3",
                "description": "minimum",
                "objective": {"reward_mode": "sum", "short_stem_penalty": 0.0, "min_stem_length": 3},
            },
        ],
    }
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(audit, "run_rnafold", lambda sequence, **kwargs: {
        "success": True,
        "reference_structure": "." * len(sequence),
        "reference_energy": 0.0,
        "backend": "mock",
    })

    result = audit.run_equal_budget_audit(run_id="smoke", config_path=config_path)
    output = Path(result["output_dir"])
    decision = audit.json.loads((output / "selection_decision.json").read_text(encoding="utf-8"))
    assert decision["phase50_final_test_used"] is False
    assert decision["lock_recommended"] is True
    assert (output / "locked_objective_config.yaml").exists()
    assert (output / "paired_sequence_deltas.csv").exists()

    config["budget"]["sa_steps"] = 6
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Refusing stale resume"):
        audit.run_equal_budget_audit(run_id="smoke", config_path=config_path)
