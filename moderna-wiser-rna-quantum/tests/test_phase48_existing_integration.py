import json
from pathlib import Path

from src.evaluation import strict_classical_pipeline
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.exact_solver import solve_stem_qubo_exact
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import solve_stem_qubo_simulated_annealing


SEQUENCE = "GGGAAAUCC"


def test_existing_model_sample_behavior_is_preserved() -> None:
    qubo = build_stem_qubo(SEQUENCE)
    assert qubo["num_variables"] == 3
    assert len(qubo["quadratic_terms"]) == 3

    greedy = solve_stem_qubo_greedy(SEQUENCE)
    annealing = solve_stem_qubo_simulated_annealing(SEQUENCE, num_steps=1000)
    exact = solve_stem_qubo_exact(SEQUENCE)

    assert greedy["predicted_structure"] == "(((...)))"
    assert annealing["predicted_structure"] == "(((...)))"
    assert exact["predicted_structure"] == "(((...)))"
    assert greedy["best_energy"] == -7.0
    assert annealing["best_energy"] == -7.0
    assert exact["best_energy"] == -7.0


def test_complete_pipeline_writes_required_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        strict_classical_pipeline,
        "run_rnafold",
        lambda *args, **kwargs: {
            "sequence": SEQUENCE,
            "reference_structure": "(((...)))",
            "reference_energy": -3.4,
            "runtime_seconds": 0.001,
            "success": True,
            "status": "success",
            "error": None,
            "backend": "test fixture",
            "warnings": [],
        },
    )

    result = strict_classical_pipeline.run_pipeline(
        sequence=SEQUENCE,
        run_id="test_run",
        output_folder=tmp_path,
        config_path=None,
    )

    run_dir = Path(result["output_dir"])
    for filename in strict_classical_pipeline.REQUIRED_OUTPUTS:
        assert (run_dir / filename).exists(), filename

    structural = json.loads((run_dir / "structural_comparison.json").read_text())
    assert structural["f1_score"] == 1.0
    assert result["strict_complete"] is True
