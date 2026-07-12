from __future__ import annotations

import json
from pathlib import Path
from src.evaluation.experiment_report_writer import build_experiment_report, save_experiment_outputs, write_csv_rows, write_json, write_text


def test_write_json_creates_file(tmp_path: Path):
    output = write_json(tmp_path / "example.json", {"a": 1})
    assert json.loads(output.read_text(encoding="utf-8"))["a"] == 1


def test_write_text_creates_file(tmp_path: Path):
    output = write_text(tmp_path / "example.txt", "hello")
    assert output.read_text(encoding="utf-8") == "hello"


def test_write_csv_rows_creates_file(tmp_path: Path):
    output = write_csv_rows(tmp_path / "example.csv", [{"name": "a", "value": 1}], ["name", "value"])
    assert "name,value" in output.read_text(encoding="utf-8")


def test_build_experiment_report_contains_key_sections():
    report = build_experiment_report(
        run_id="test_run",
        sequence="GGGAAAUCC",
        vienna_reference={"success": False, "reference_structure": None, "reference_energy": None, "runtime_seconds": 0.0, "error": "RNAfold missing"},
        predicted_structure={"predicted_dotbracket": ".........", "predicted_pairs": [], "solver": "sample", "qubo_energy": None},
        structural_comparison={"comparison_available": False, "exact_match": False, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "base_pair_distance": None},
        energy_comparison={"comparison_available": False, "reference_energy": None, "qubo_energy": None, "energy_difference": None, "absolute_energy_difference": None},
        runtime_summary={"step_count": 0, "total_runtime_seconds": 0.0, "slowest_step": None},
        config={"mode": "test"},
    )
    assert "Strict Classical Foundation Experiment Report" in report
    assert "ViennaRNA Reference" in report
    assert "Safe Claim Boundary" in report


def test_save_experiment_outputs_creates_expected_files(tmp_path: Path):
    paths = save_experiment_outputs(
        output_dir=tmp_path,
        run_id="test_run",
        sequence="GGGAAAUCC",
        vienna_reference={"sequence": "GGGAAAUCC", "reference_structure": None, "reference_energy": None, "runtime_seconds": 0.0, "success": False, "error": "RNAfold missing", "raw_output": ""},
        candidate_pairs=[{"pair_id": 0, "i": 0, "j": 8}],
        candidate_stems=[{"stem_id": 0, "pairs": "[[0, 8]]"}],
        qubo_summary=[{"term_type": "linear", "var_i": 0, "var_j": 0, "coefficient": -1.0}],
        solver_results=[{"solver": "sample", "energy": -1.0, "bitstring": "[1]"}],
        predicted_structure={"predicted_dotbracket": "(.......)", "predicted_pairs": [(0, 8)], "solver": "sample", "qubo_energy": -1.0},
        structural_comparison={"comparison_available": False, "exact_match": False, "precision": 0.0, "recall": 0.0, "f1_score": 0.0, "base_pair_distance": None},
        energy_comparison={"comparison_available": False, "reference_energy": None, "qubo_energy": -1.0, "energy_difference": None, "absolute_energy_difference": None},
        runtime_summary={"step_count": 0, "total_runtime_seconds": 0.0, "slowest_step": None, "step_timings": {}},
        config={"mode": "test"},
    )
    assert "experiment_report" in paths
    for path in paths.values():
        assert Path(path).exists()
