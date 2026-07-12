from __future__ import annotations

from pathlib import Path

import yaml

import src.evaluation.phase50B_objective_ablation as phase50b


def test_ranking_prioritizes_control_preservation():
    preserved = {
        "variant_id": "preserved", "success_rate": 1.0,
        "controls_preserved": True, "mixed_mean_best_known_f1": 0.4,
        "dev_mixed_18_f1": 0.4, "micro_f1": 0.5,
        "false_positives": 2, "false_negatives": 2,
        "mean_sa_best_energy_hit_rate": 0.5,
        "mean_sa_unique_structure_count": 3,
        "mean_qubo_variable_count": 10, "mean_runtime_seconds": 1,
    }
    broken = dict(preserved)
    broken.update({
        "variant_id": "broken", "controls_preserved": False,
        "mixed_mean_best_known_f1": 0.9,
    })
    assert phase50b.ranking_key(preserved) < phase50b.ranking_key(broken)


def test_load_development_dataset_excludes_final_test(tmp_path: Path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,split,category,source_type,sequence,notes\n"
        "dev_a,development,unstructured_control,synthetic,AAAA,dev\n"
        "test_a,final_test,unstructured_control,synthetic,UUUU,test\n",
        encoding="utf-8",
    )
    rows = phase50b.load_development_dataset(dataset)
    assert [row["sequence_id"] for row in rows] == ["dev_a"]


def test_smoke_ablation_writes_locked_development_result(tmp_path: Path, monkeypatch):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,split,category,source_type,sequence,notes\n"
        "dev_a,development,unstructured_control,synthetic,AAAAAAAA,dev\n"
        "test_u,final_test,unstructured_control,synthetic,UUUUUUUU,test\n",
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
    config = tmp_path / "ablation.yaml"
    config.write_text(
        yaml.safe_dump({
            "dataset_path": str(dataset),
            "strict_config_path": str(strict),
            "output_root": str(output_root),
            "resume": False,
            "top_k": 1,
            "exact_max_variables": 20,
            "screen": {
                "sa_seeds": [3], "sa_steps": 5,
                "sa_initial_temperature": 1.0, "sa_final_temperature": 0.01,
                "sa_cooling_rate": 0.9, "run_local_refinement": True,
            },
            "confirmation": {
                "sa_seeds": [7], "sa_steps": 5,
                "sa_initial_temperature": 1.0, "sa_final_temperature": 0.01,
                "sa_cooling_rate": 0.9, "run_local_refinement": True,
            },
            "variants": [{
                "id": "baseline_sum", "description": "baseline",
                "objective": {"reward_mode": "sum", "min_stem_length": 2},
            }],
        }, sort_keys=False),
        encoding="utf-8",
    )

    monkeypatch.setattr(phase50b, "run_rnafold", lambda sequence, **kwargs: {
        "success": True,
        "reference_structure": "." * len(sequence),
        "reference_energy": 0.0,
        "backend": "mock",
    })
    result = phase50b.run_ablation(run_id="smoke", config_path=config)
    out = Path(result["output_dir"])
    assert (out / "selected_objective.json").exists()
    assert (out / "selected_objective_config.yaml").exists()
    selected = phase50b.json.loads((out / "selected_objective.json").read_text(encoding="utf-8"))
    assert selected["phase50_final_test_used"] is False
