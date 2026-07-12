import csv
from pathlib import Path

import pytest
import yaml

from src.evaluation.phase49_benchmark import load_dataset, run_benchmark
from src.evaluation.phase49_parameter_sweep import _parameter_combinations


def _write_dataset(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["sequence_id", "split", "category", "source_type", "sequence", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_dataset_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "dataset.csv"
    _write_dataset(
        path,
        [
            {"sequence_id": "x", "split": "calibration", "category": "a", "source_type": "s", "sequence": "AAAA", "notes": ""},
            {"sequence_id": "x", "split": "validation", "category": "b", "source_type": "s", "sequence": "CCCC", "notes": ""},
        ],
    )
    with pytest.raises(ValueError, match="Duplicate sequence_id"):
        load_dataset(path)


def test_parameter_grid_expands_cartesian_product():
    combos = _parameter_combinations({"a": [1, 2], "b": [3, 4, 5]})
    assert len(combos) == 6
    assert {tuple(sorted(item.items())) for item in combos}


def test_benchmark_runner_writes_aggregate_outputs(tmp_path):
    dataset = tmp_path / "dataset.csv"
    _write_dataset(
        dataset,
        [
            {"sequence_id": "empty", "split": "calibration", "category": "control", "source_type": "synthetic", "sequence": "AAAAAAAAAAAA", "notes": ""},
            {"sequence_id": "hairpin", "split": "calibration", "category": "hairpin", "source_type": "synthetic", "sequence": "GCGCUUCGGCGC", "notes": ""},
        ],
    )
    strict_config = tmp_path / "strict.yaml"
    strict_config.write_text(yaml.safe_dump({"min_loop_length": 3}), encoding="utf-8")

    def fake_runner(*, sequence, run_id, output_folder, config_path):
        run_dir = Path(output_folder) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        structure = "." * len(sequence) if set(sequence) == {"A"} else "((((....))))"
        pair_count = 0 if structure.startswith(".") else 4
        with (run_dir / "solver_results.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["solver", "status", "energy", "predicted_structure"])
            writer.writeheader()
            writer.writerow({"solver": "exact stem-QUBO enumeration", "status": "success", "energy": -1.0, "predicted_structure": structure})
            writer.writerow({"solver": "greedy stem-QUBO baseline", "status": "success", "energy": -1.0, "predicted_structure": structure})
        return {
            "strict_complete": True,
            "vienna": {"backend": "fake", "reference_structure": structure, "reference_energy": -1.0, "error": None},
            "predicted_structure": structure,
            "qubo_energy": -1.0,
            "best_solver": "exact stem-QUBO enumeration",
            "structural_comparison": {
                "reference_pair_count": pair_count,
                "predicted_pair_count": pair_count,
                "true_positives": pair_count,
                "false_positives": 0,
                "false_negatives": 0,
                "precision": 1.0,
                "recall": 1.0,
                "f1_score": 1.0,
                "exact_match": True,
                "base_pair_distance": 0,
            },
            "runtime_summary": {
                "candidate_pair_count": pair_count,
                "candidate_stem_count": 1 if pair_count else 0,
                "qubo_variable_count": 1 if pair_count else 0,
                "quadratic_term_count": 0,
                "exact_state_estimate": 2 if pair_count else 1,
                "total_runtime_seconds": 0.01,
            },
        }

    result = run_benchmark(
        dataset_path=dataset,
        split="calibration",
        strict_config_path=strict_config,
        run_id="test_run",
        output_root=tmp_path / "results",
        resume=False,
        pipeline_runner=fake_runner,
    )

    run_dir = Path(result["run_dir"])
    assert result["summary"]["micro_f1"] == 1.0
    assert result["summary"]["exact_match_rate"] == 1.0
    assert (run_dir / "benchmark_results.csv").exists()
    assert (run_dir / "benchmark_summary.json").exists()
    assert (run_dir / "scaling_summary.json").exists()
    assert (run_dir / "benchmark_report.md").exists()
