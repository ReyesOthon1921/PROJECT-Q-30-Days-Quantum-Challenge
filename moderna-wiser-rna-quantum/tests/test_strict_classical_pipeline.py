from __future__ import annotations

from pathlib import Path
from src.evaluation.strict_classical_pipeline import generate_candidate_pairs, generate_candidate_stems, load_config, run_pipeline


def test_generate_candidate_pairs_returns_candidates():
    pairs = generate_candidate_pairs("GGGAAAUCC", min_loop_length=3, allow_wobble=True)
    assert len(pairs) > 0
    assert {"pair_id", "i", "j", "pair_type", "score"}.issubset(pairs[0].keys())


def test_generate_candidate_stems_returns_candidates():
    pairs = generate_candidate_pairs("GGGAAAUCC", min_loop_length=3, allow_wobble=True)
    stems = generate_candidate_stems(pairs, stem_min_length=2)
    assert len(stems) > 0
    assert {"stem_id", "pairs", "score"}.issubset(stems[0].keys())


def test_run_pipeline_creates_outputs(tmp_path: Path):
    config = load_config(None)
    config["simulated_annealing_steps"] = 25
    result = run_pipeline("GGGAAAUCC", "pytest_run", config, output_root=str(tmp_path))
    assert result["success"] is True
    assert Path(result["output_dir"]).exists()
    assert (Path(result["output_dir"]) / "experiment_report.md").exists()
    assert (Path(result["output_dir"]) / "candidate_pairs.csv").exists()
    assert (Path(result["output_dir"]) / "solver_results.csv").exists()
