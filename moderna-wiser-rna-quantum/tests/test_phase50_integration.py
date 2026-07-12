from __future__ import annotations

import csv
from pathlib import Path

import yaml

import src.evaluation.phase50_solver_diagnostics as phase50


def test_dataset_splits_are_separate():
    development = phase50.load_dataset("data/benchmarks/phase50_solver_diagnostics_sequences.csv", "development")
    final_test = phase50.load_dataset("data/benchmarks/phase50_solver_diagnostics_sequences.csv", "final_test")
    assert development
    assert final_test
    assert {row["sequence_id"] for row in development}.isdisjoint({row["sequence_id"] for row in final_test})


def test_runner_writes_required_outputs(tmp_path, monkeypatch):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text(
        "sequence_id,split,category,source_type,sequence,notes\n"
        "tiny,development,designed_hairpin,test,GCGCUUCGGCGC,tiny\n",
        encoding="utf-8",
    )
    strict = tmp_path / "strict.yaml"
    strict.write_text(
        "min_loop_length: 3\nallow_wobble: true\nstem_min_length: 2\n"
        "overlap_penalty: 14.0\ncrossing_penalty: 12.0\n"
        "rnafold_executable: RNAfold\nallow_vienna_python_fallback: true\n",
        encoding="utf-8",
    )
    output_root = tmp_path / "out"
    config = tmp_path / "phase50.yaml"
    with config.open("w", encoding="utf-8") as handle:
        yaml.safe_dump({
            "dataset_path": str(dataset), "strict_config_path": str(strict),
            "output_root": str(output_root), "sa_seeds": [1,2], "sa_steps": 50,
            "sa_initial_temperature": 5.0, "sa_final_temperature": 0.01,
            "sa_cooling_rate": 0.95, "run_local_refinement": True,
            "exact_max_variables": 20, "energy_tolerance": 1e-9,
        }, handle)
    monkeypatch.setattr(phase50, "run_rnafold", lambda *args, **kwargs: {
        "success": True, "status": "success", "error": None,
        "backend": "mock", "reference_structure": "((((....))))",
        "reference_energy": -5.5,
    })
    result = phase50.run_diagnostics("development", "test_run", config)
    out = Path(result["output_dir"])
    required = {
        "dataset_snapshot.csv", "effective_phase50_config.yaml",
        "effective_strict_config.yaml", "sequence_summary.csv", "sa_runs.csv",
        "structure_frequencies.csv", "energy_decomposition.csv",
        "diagnostic_summary.json", "diagnostic_report.md", "failed_runs.csv",
    }
    assert required.issubset({path.name for path in out.iterdir()})
    with (out/"sa_runs.csv").open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2
