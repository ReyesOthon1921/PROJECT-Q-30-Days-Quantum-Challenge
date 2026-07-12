"""One-command Phase 48 strict classical foundation pipeline.

This implementation is adapted to the project's existing modules instead of
replacing its candidate generation, stem-QUBO formulation, greedy solver, or
simulated-annealing solver.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence
from src.classical.vienna_rnafold import run_rnafold
from src.evaluation.energy_comparison import compare_energy
from src.evaluation.structural_comparison import compare_structures
from src.qubo.build_qubo import build_stem_qubo
from src.qubo.candidate_pairs import generate_candidate_pairs
from src.qubo.candidate_stems import generate_candidate_stems
from src.solvers.exact_solver import solve_stem_qubo_exact
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import solve_stem_qubo_simulated_annealing

DEFAULT_CONFIG: dict[str, Any] = {
    "sequence": "GGGAAAUCC",
    "min_loop_length": 3,
    "allow_wobble": True,
    "candidate_mode": "stems",
    "stem_min_length": 2,
    "overlap_penalty": 10.0,
    "crossing_penalty": 8.0,
    "solver_exact_max_variables": 20,
    "run_greedy": True,
    "run_simulated_annealing": True,
    "simulated_annealing_steps": 8000,
    "simulated_annealing_initial_temperature": 10.0,
    "simulated_annealing_final_temperature": 0.01,
    "simulated_annealing_cooling_rate": 0.995,
    "random_seed": 7,
    "rnafold_executable": "RNAfold",
    "allow_vienna_python_fallback": True,
    "notes": "Strict classical foundation using the existing stem-QUBO model.",
}

REQUIRED_OUTPUTS = (
    "input_sequence.txt",
    "vienna_reference.json",
    "candidate_pairs.csv",
    "candidate_stems.csv",
    "qubo_summary.csv",
    "solver_results.csv",
    "predicted_structure.json",
    "structural_comparison.json",
    "energy_comparison.json",
    "runtime_summary.json",
    "experiment_report.md",
)


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(_jsonable(payload), handle, indent=2, sort_keys=True)
        handle.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            prepared: dict[str, Any] = {}
            for field in fieldnames:
                value = row.get(field, "")
                if isinstance(value, (list, tuple, dict)):
                    value = json.dumps(_jsonable(value), sort_keys=True)
                prepared[field] = value
            writer.writerow(prepared)


def _safe_run_id(raw_run_id: str | None) -> str:
    candidate = raw_run_id or datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate).strip("._")
    if not cleaned:
        raise ValueError("run-id must contain at least one letter or number.")
    return cleaned


def _load_config(path: Path | None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if path is None:
        default_path = REPO_ROOT / "configs" / "strict_classical_foundation.yaml"
        path = default_path if default_path.exists() else None

    if path is not None:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "PyYAML is required to load the Phase 48 configuration. "
                "Install it with: python -m pip install PyYAML"
            ) from exc

        with path.open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Configuration root must be a mapping: {path}")
        config.update(loaded)
        config["config_path"] = str(path)
    else:
        config["config_path"] = None

    return config


def _solver_energy(result: dict[str, Any]) -> float | None:
    for key in ("best_energy", "objective_score"):
        value = result.get(key)
        if value is not None:
            return float(value)
    return None


def _solver_status(result: dict[str, Any]) -> str:
    if result.get("skipped"):
        return "skipped"
    if result.get("success", True):
        return "success"
    return "failed"


def _select_best_solver(results: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        result
        for result in results
        if _solver_status(result) == "success"
        and _solver_energy(result) is not None
        and result.get("predicted_structure") is not None
    ]
    if not candidates:
        raise RuntimeError("No classical solver produced a decodable prediction.")

    solver_priority = {
        "exact stem-QUBO enumeration": 0,
        "simulated annealing stem-QUBO baseline": 1,
        "greedy stem-QUBO baseline": 2,
    }
    return min(
        candidates,
        key=lambda item: (
            _solver_energy(item),
            solver_priority.get(str(item.get("solver")), 99),
        ),
    )


def _qubo_rows(qubo: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for variable, coefficient in qubo["linear_terms"].items():
        rows.append(
            {
                "term_type": "linear",
                "var_a": variable,
                "var_b": "",
                "coefficient": coefficient,
                "reasons": "stem reward",
            }
        )
    for term in qubo["quadratic_terms"]:
        rows.append(
            {
                "term_type": "quadratic",
                "var_a": term["var_a"],
                "var_b": term["var_b"],
                "coefficient": term["coefficient"],
                "reasons": term["reasons"],
            }
        )
    return rows


def _solver_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for result in results:
        rows.append(
            {
                "solver": result.get("solver"),
                "status": _solver_status(result),
                "energy": _solver_energy(result),
                "runtime_seconds": result.get("runtime_seconds"),
                "candidate_stems": result.get("total_candidate_stems"),
                "qubo_variables": result.get("total_qubo_variables"),
                "quadratic_penalties": result.get("total_quadratic_penalties"),
                "selected_stems": result.get("selected_stem_count"),
                "selected_pairs": result.get("selected_pair_count"),
                "predicted_structure": result.get("predicted_structure"),
                "is_conflict_free": result.get("is_conflict_free", True),
                "assignments_evaluated": result.get("assignments_evaluated"),
                "error": result.get("error") or result.get("structure_error"),
            }
        )
    return rows


def _report_markdown(
    sequence: str,
    config: dict[str, Any],
    vienna: dict[str, Any],
    best: dict[str, Any],
    structural: dict[str, Any] | None,
    energy: dict[str, Any] | None,
    runtimes: dict[str, Any],
    output_dir: Path,
) -> str:
    lines = [
        "# Strict Classical Foundation Experiment Report",
        "",
        f"- Run directory: `{output_dir}`",
        f"- Sequence: `{sequence}`",
        f"- Sequence length: {len(sequence)}",
        f"- Selected solver: {best.get('solver')}",
        f"- Predicted structure: `{best.get('predicted_structure')}`",
        f"- QUBO objective: {_solver_energy(best)}",
        "",
        "## ViennaRNA reference",
        "",
        f"- Success: {vienna.get('success')}",
        f"- Status: {vienna.get('status')}",
        f"- Backend: {vienna.get('backend')}",
        f"- Reference structure: `{vienna.get('reference_structure')}`",
        f"- Reference MFE: {vienna.get('reference_energy')}",
        f"- Error: {vienna.get('error')}",
        "",
        "## Structural comparison",
        "",
    ]

    if structural is None:
        lines.append("Not available because the ViennaRNA reference did not complete.")
    else:
        for key in (
            "reference_pair_count",
            "predicted_pair_count",
            "true_positives",
            "false_positives",
            "false_negatives",
            "precision",
            "recall",
            "f1_score",
            "exact_match",
            "base_pair_distance",
        ):
            lines.append(f"- {key}: {structural.get(key)}")

    lines.extend(["", "## Energy comparison", ""])
    if energy is None:
        lines.append("Not available because the ViennaRNA reference did not complete.")
    else:
        lines.extend(
            [
                f"- ViennaRNA MFE: {energy.get('reference_energy')}",
                f"- QUBO objective: {energy.get('qubo_energy')}",
                f"- Numerical difference: {energy.get('energy_difference')}",
                f"- Note: {energy.get('note')}",
            ]
        )

    lines.extend(
        [
            "",
            "## Runtime and scaling",
            "",
            f"- Total runtime seconds: {runtimes.get('total_runtime_seconds')}",
            f"- Candidate pairs: {runtimes.get('candidate_pair_count')}",
            f"- Candidate stems / QUBO variables: {runtimes.get('candidate_stem_count')}",
            f"- Quadratic penalties: {runtimes.get('quadratic_term_count')}",
            f"- Exact-state estimate: {runtimes.get('exact_state_estimate')}",
            "",
            "## Safe claim boundary",
            "",
            "This run demonstrates an automated and reproducible classical benchmark "
            "pipeline. It does not prove quantum advantage, experimental biological "
            "validity, or physical equivalence between the QUBO score and ViennaRNA "
            "free energy.",
            "",
            "## Configuration",
            "",
            "```json",
            json.dumps(_jsonable(config), indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def run_pipeline(
    sequence: str,
    run_id: str | None = None,
    output_folder: str | Path = "results/classical_foundation",
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute the complete strict classical workflow and save every output."""

    total_started = time.perf_counter()
    config = _load_config(Path(config_path) if config_path else None)
    cleaned = clean_sequence(sequence or str(config.get("sequence", "")))

    if not validate_rna_sequence(cleaned):
        raise ValueError("Invalid RNA sequence. Use only A, U, G, and C.")

    if str(config.get("candidate_mode", "stems")).lower() != "stems":
        raise ValueError(
            "This integration currently supports candidate_mode: stems because it "
            "reuses the project's existing stem-QUBO representation."
        )

    safe_run_id = _safe_run_id(run_id)
    output_root = Path(output_folder)
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root
    output_dir = output_root / safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "input_sequence.txt").write_text(cleaned + "\n", encoding="utf-8")

    stage_runtime: dict[str, float] = {}

    started = time.perf_counter()
    vienna = run_rnafold(
        cleaned,
        executable=str(config["rnafold_executable"]),
        allow_python_fallback=bool(config["allow_vienna_python_fallback"]),
    )
    stage_runtime["vienna_reference"] = round(time.perf_counter() - started, 6)
    _write_json(output_dir / "vienna_reference.json", vienna)

    started = time.perf_counter()
    candidate_pairs = generate_candidate_pairs(
        cleaned,
        min_loop_length=int(config["min_loop_length"]),
        allow_wobble=bool(config["allow_wobble"]),
    )
    stage_runtime["candidate_pairs"] = round(time.perf_counter() - started, 6)
    _write_csv(
        output_dir / "candidate_pairs.csv",
        candidate_pairs,
        [
            "variable_index",
            "variable_name",
            "i",
            "j",
            "left_base",
            "right_base",
            "pair_type",
            "distance",
        ],
    )

    started = time.perf_counter()
    candidate_stems = generate_candidate_stems(
        cleaned,
        min_stem_length=int(config["stem_min_length"]),
        min_loop_length=int(config["min_loop_length"]),
        allow_wobble=bool(config["allow_wobble"]),
    )
    stage_runtime["candidate_stems"] = round(time.perf_counter() - started, 6)
    _write_csv(
        output_dir / "candidate_stems.csv",
        candidate_stems,
        [
            "stem_index",
            "variable_name",
            "length",
            "start_pair",
            "end_pair",
            "pairs",
            "pair_types",
        ],
    )

    started = time.perf_counter()
    qubo = build_stem_qubo(
        cleaned,
        overlap_penalty=float(config["overlap_penalty"]),
        crossing_penalty=float(config["crossing_penalty"]),
        min_stem_length=int(config["stem_min_length"]),
        min_loop_length=int(config["min_loop_length"]),
        allow_wobble=bool(config["allow_wobble"]),
    )
    stage_runtime["qubo_build"] = round(time.perf_counter() - started, 6)
    _write_csv(
        output_dir / "qubo_summary.csv",
        _qubo_rows(qubo),
        ["term_type", "var_a", "var_b", "coefficient", "reasons"],
    )

    solver_results: list[dict[str, Any]] = []

    started = time.perf_counter()
    exact = solve_stem_qubo_exact(
        cleaned,
        max_variables=int(config["solver_exact_max_variables"]),
        min_stem_length=int(config["stem_min_length"]),
        min_loop_length=int(config["min_loop_length"]),
        allow_wobble=bool(config["allow_wobble"]),
        overlap_penalty=float(config["overlap_penalty"]),
        crossing_penalty=float(config["crossing_penalty"]),
    )
    stage_runtime["exact_solver"] = round(time.perf_counter() - started, 6)
    solver_results.append(exact)

    if bool(config["run_greedy"]):
        started = time.perf_counter()
        greedy = solve_stem_qubo_greedy(
            cleaned,
            min_stem_length=int(config["stem_min_length"]),
            min_loop_length=int(config["min_loop_length"]),
            allow_wobble=bool(config["allow_wobble"]),
            overlap_penalty=float(config["overlap_penalty"]),
            crossing_penalty=float(config["crossing_penalty"]),
        )
        stage_runtime["greedy_solver"] = round(time.perf_counter() - started, 6)
        solver_results.append(greedy)

    if bool(config["run_simulated_annealing"]):
        started = time.perf_counter()
        annealing = solve_stem_qubo_simulated_annealing(
            cleaned,
            num_steps=int(config["simulated_annealing_steps"]),
            initial_temperature=float(
                config["simulated_annealing_initial_temperature"]
            ),
            final_temperature=float(config["simulated_annealing_final_temperature"]),
            cooling_rate=float(config["simulated_annealing_cooling_rate"]),
            seed=int(config["random_seed"]),
            min_stem_length=int(config["stem_min_length"]),
            min_loop_length=int(config["min_loop_length"]),
            allow_wobble=bool(config["allow_wobble"]),
            overlap_penalty=float(config["overlap_penalty"]),
            crossing_penalty=float(config["crossing_penalty"]),
        )
        stage_runtime["simulated_annealing_solver"] = round(
            time.perf_counter() - started, 6
        )
        solver_results.append(annealing)

    _write_csv(
        output_dir / "solver_results.csv",
        _solver_rows(solver_results),
        [
            "solver",
            "status",
            "energy",
            "runtime_seconds",
            "candidate_stems",
            "qubo_variables",
            "quadratic_penalties",
            "selected_stems",
            "selected_pairs",
            "predicted_structure",
            "is_conflict_free",
            "assignments_evaluated",
            "error",
        ],
    )

    best = _select_best_solver(solver_results)
    predicted = {
        "sequence": cleaned,
        "solver": best.get("solver"),
        "qubo_energy": _solver_energy(best),
        "predicted_structure": best.get("predicted_structure"),
        "selected_pair_count": best.get("selected_pair_count"),
        "selected_pairs": best.get("selected_pairs", []),
        "selected_stem_count": best.get("selected_stem_count"),
        "selected_stems": best.get("selected_stems", []),
        "is_conflict_free": best.get("is_conflict_free", True),
        "score_note": (
            "The QUBO value is the project's heuristic stem-selection objective, "
            "not a thermodynamic free-energy estimate."
        ),
    }
    _write_json(output_dir / "predicted_structure.json", predicted)

    structural: dict[str, Any] | None = None
    energy: dict[str, Any] | None = None

    if vienna.get("success"):
        structural = compare_structures(
            str(vienna["reference_structure"]),
            str(best["predicted_structure"]),
        )
        energy = compare_energy(
            float(vienna["reference_energy"]),
            float(_solver_energy(best)),
        )
        _write_json(output_dir / "structural_comparison.json", structural)
        _write_json(output_dir / "energy_comparison.json", energy)
    else:
        _write_json(
            output_dir / "structural_comparison.json",
            {
                "success": False,
                "error": "ViennaRNA reference unavailable; comparison not computed.",
                "vienna_error": vienna.get("error"),
            },
        )
        _write_json(
            output_dir / "energy_comparison.json",
            {
                "success": False,
                "error": "ViennaRNA reference unavailable; comparison not computed.",
                "vienna_error": vienna.get("error"),
            },
        )

    runtime_summary = {
        "run_id": safe_run_id,
        "sequence_length": len(cleaned),
        "candidate_pair_count": len(candidate_pairs),
        "candidate_stem_count": len(candidate_stems),
        "qubo_variable_count": qubo["num_variables"],
        "quadratic_term_count": len(qubo["quadratic_terms"]),
        "exact_state_estimate": (
            2 ** qubo["num_variables"]
            if qubo["num_variables"] <= int(config["solver_exact_max_variables"])
            else None
        ),
        "stage_runtime_seconds": stage_runtime,
        "total_runtime_seconds": round(time.perf_counter() - total_started, 6),
        "python_version": sys.version,
        "vienna_backend": vienna.get("backend"),
        "vienna_success": vienna.get("success"),
        "config": config,
    }
    _write_json(output_dir / "runtime_summary.json", runtime_summary)

    report = _report_markdown(
        cleaned,
        config,
        vienna,
        best,
        structural,
        energy,
        runtime_summary,
        output_dir,
    )
    (output_dir / "experiment_report.md").write_text(report, encoding="utf-8")

    missing_outputs = [
        name for name in REQUIRED_OUTPUTS if not (output_dir / name).exists()
    ]
    if missing_outputs:
        raise RuntimeError(f"Required outputs were not created: {missing_outputs}")

    return {
        "success": bool(vienna.get("success")),
        "strict_complete": bool(vienna.get("success")),
        "run_id": safe_run_id,
        "output_dir": str(output_dir),
        "sequence": cleaned,
        "vienna": vienna,
        "best_solver": best.get("solver"),
        "predicted_structure": best.get("predicted_structure"),
        "qubo_energy": _solver_energy(best),
        "structural_comparison": structural,
        "energy_comparison": energy,
        "runtime_summary": runtime_summary,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Phase 48 strict classical RNA/QUBO foundation."
    )
    parser.add_argument("--sequence", required=True, help="RNA sequence using A/U/G/C.")
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--output-folder",
        default="results/classical_foundation",
    )
    parser.add_argument("--config", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    try:
        result = run_pipeline(
            sequence=args.sequence,
            run_id=args.run_id,
            output_folder=args.output_folder,
            config_path=args.config,
        )
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[OK] Results saved to: {result['output_dir']}")
    print(f"[OK] Selected solver: {result['best_solver']}")
    print(f"[OK] Predicted structure: {result['predicted_structure']}")

    if result["strict_complete"]:
        print("[OK] ViennaRNA reference and both comparisons completed.")
        return 0

    print("[WARNING] Solver outputs were saved, but ViennaRNA was unavailable.")
    print(f"[WARNING] {result['vienna'].get('error')}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
