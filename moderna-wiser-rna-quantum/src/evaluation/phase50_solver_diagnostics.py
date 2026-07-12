"""Phase 50A solver-robustness diagnostics for the RNA stem-QUBO model.

This phase deliberately diagnoses solver behavior before changing the objective.
It uses a new development dataset and does not tune against the frozen Phase 49
validation split.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence
from src.classical.vienna_rnafold import run_rnafold
from src.evaluation.structural_comparison import compare_structures
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.exact_solver import solve_stem_qubo_exact
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import (
    calculate_qubo_energy,
    decode_solution_to_structure,
)

DEFAULT_CONFIG: dict[str, Any] = {
    "dataset_path": "data/benchmarks/phase50_solver_diagnostics_sequences.csv",
    "strict_config_path": "configs/phase50_locked_phase49_config.yaml",
    "output_root": "results/phase50_solver_diagnostics",
    "resume": True,
    "fail_fast": False,
    "development_split": "development",
    "sa_seeds": [3, 7, 11, 19, 23, 29, 31, 37, 41, 43, 47, 53],
    "sa_steps": 6000,
    "sa_initial_temperature": 10.0,
    "sa_final_temperature": 0.01,
    "sa_cooling_rate": 0.995,
    "run_local_refinement": True,
    "exact_max_variables": 20,
    "energy_tolerance": 1.0e-9,
}

SEQUENCE_FIELDS = [
    "sequence_id", "split", "category", "sequence", "sequence_length",
    "status", "error", "vienna_backend", "reference_structure",
    "reference_energy", "candidate_stem_count", "qubo_variable_count",
    "quadratic_term_count", "exact_status", "exact_energy", "exact_f1",
    "greedy_energy", "greedy_f1", "sa_run_count", "sa_success_count",
    "sa_raw_best_energy", "sa_refined_best_energy", "sa_mean_refined_energy",
    "sa_worst_refined_energy", "sa_energy_std", "sa_unique_structure_count",
    "sa_modal_structure", "sa_modal_structure_frequency",
    "sa_best_energy_hit_rate", "sa_best_f1", "best_known_energy",
    "best_known_structure", "best_known_f1", "greedy_energy_gap",
    "exact_energy_gap", "diagnosis", "runtime_seconds", "run_directory",
]

SA_FIELDS = [
    "sequence_id", "seed", "status", "error", "raw_energy", "refined_energy",
    "raw_structure", "refined_structure", "raw_f1", "refined_f1",
    "accepted_moves", "local_refinement_flips", "selected_stem_count",
    "is_conflict_free", "runtime_seconds",
]

FREQUENCY_FIELDS = [
    "sequence_id", "structure", "count", "frequency", "best_energy",
    "mean_energy", "best_f1", "is_modal",
]

DECOMPOSITION_FIELDS = [
    "sequence_id", "solver", "seed", "total_energy", "recomputed_energy",
    "linear_reward", "quadratic_penalty", "overlap_penalty_contribution",
    "crossing_penalty_contribution", "selected_variable_count",
    "is_conflict_free", "predicted_structure",
]


def _resolve(path: str | Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else REPO_ROOT / value


def _safe_id(raw: str | None, prefix: str) -> str:
    candidate = raw or datetime.now(timezone.utc).strftime(f"{prefix}_%Y%m%dT%H%M%SZ")
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", candidate).strip("._")
    if not cleaned:
        raise ValueError("Run identifier must contain a letter or number.")
    return cleaned


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyYAML is required. Install requirements-phase50.txt.") from exc
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be a mapping: {path}")
    return data


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    import yaml  # type: ignore
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True, default=str)
        handle.write("\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def load_phase50_config(path: str | Path | None = None) -> dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config_path = _resolve(path or "configs/phase50_solver_diagnostics.yaml")
    if config_path.exists():
        config.update(_load_yaml(config_path))
    config["config_path"] = str(config_path) if config_path.exists() else None
    return config


def load_strict_config(path: str | Path) -> dict[str, Any]:
    strict_path = _resolve(path)
    if not strict_path.exists():
        raise FileNotFoundError(f"Locked strict config was not found: {strict_path}")
    config = _load_yaml(strict_path)
    config["strict_config_path"] = str(strict_path)
    return config


def load_dataset(path: str | Path, split: str) -> list[dict[str, str]]:
    dataset_path = _resolve(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Phase 50 dataset was not found: {dataset_path}")
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"sequence_id", "split", "category", "sequence"}
    if rows and not required.issubset(rows[0]):
        raise ValueError(f"Dataset is missing required columns: {sorted(required-set(rows[0]))}")
    result = []
    seen: set[str] = set()
    for row in rows:
        sequence_id = str(row.get("sequence_id", "")).strip()
        row_split = str(row.get("split", "")).strip().lower()
        if row_split != split.lower():
            continue
        if not sequence_id or sequence_id in seen:
            raise ValueError(f"Missing or duplicate sequence_id: {sequence_id}")
        seen.add(sequence_id)
        sequence = clean_sequence(str(row.get("sequence", "")))
        if not validate_rna_sequence(sequence):
            raise ValueError(f"Invalid sequence for {sequence_id}: {sequence}")
        result.append({
            "sequence_id": sequence_id,
            "split": row_split,
            "category": str(row.get("category", "unknown")).strip() or "unknown",
            "source_type": str(row.get("source_type", "synthetic")).strip() or "synthetic",
            "notes": str(row.get("notes", "")).strip(),
            "sequence": sequence,
        })
    return result


def build_adjacency(
    variable_names: list[str],
    linear_terms: dict[str, float],
    quadratic_terms: list[dict[str, Any]],
) -> tuple[list[float], list[list[tuple[int, float]]]]:
    index = {name: position for position, name in enumerate(variable_names)}
    linear = [float(linear_terms[name]) for name in variable_names]
    adjacency: list[list[tuple[int, float]]] = [[] for _ in variable_names]
    for term in quadratic_terms:
        left = index[term["var_a"]]
        right = index[term["var_b"]]
        coefficient = float(term["coefficient"])
        adjacency[left].append((right, coefficient))
        adjacency[right].append((left, coefficient))
    return linear, adjacency


def flip_delta(
    index: int,
    state: list[int],
    linear: list[float],
    adjacency: list[list[tuple[int, float]]],
) -> float:
    local_field = linear[index] + sum(
        coefficient * state[neighbor]
        for neighbor, coefficient in adjacency[index]
    )
    return (1 - 2 * state[index]) * local_field


def state_to_solution(variable_names: list[str], state: list[int]) -> dict[str, int]:
    return dict(zip(variable_names, state))


def one_flip_descent(
    state: list[int],
    linear: list[float],
    adjacency: list[list[tuple[int, float]]],
    tolerance: float = 1.0e-12,
) -> tuple[list[int], int]:
    refined = list(state)
    flips = 0
    while True:
        deltas = [flip_delta(i, refined, linear, adjacency) for i in range(len(refined))]
        best_index = min(range(len(deltas)), key=deltas.__getitem__, default=None)
        if best_index is None or deltas[best_index] >= -tolerance:
            break
        refined[best_index] = 1 - refined[best_index]
        flips += 1
    return refined, flips


def run_fast_sa(
    qubo: dict[str, Any],
    seed: int,
    steps: int,
    initial_temperature: float,
    final_temperature: float,
    cooling_rate: float,
    run_local_refinement: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    variable_names = list(qubo["linear_terms"].keys())
    if not variable_names:
        return {
            "success": True, "status": "success", "error": None, "seed": seed,
            "raw_energy": 0.0, "refined_energy": 0.0, "raw_solution": {},
            "refined_solution": {}, "accepted_moves": 0,
            "local_refinement_flips": 0,
            "runtime_seconds": round(time.perf_counter()-started, 6),
        }
    linear, adjacency = build_adjacency(
        variable_names, qubo["linear_terms"], qubo["quadratic_terms"]
    )
    rng = random.Random(seed)
    state = [0] * len(variable_names)
    current_energy = 0.0
    best_state = list(state)
    best_energy = current_energy
    temperature = float(initial_temperature)
    accepted_moves = 0
    for _ in range(int(steps)):
        index = rng.randrange(len(state))
        delta = flip_delta(index, state, linear, adjacency)
        accept = delta <= 0.0
        if not accept:
            accept = rng.random() < math.exp(-delta/max(temperature, 1.0e-12))
        if accept:
            state[index] = 1 - state[index]
            current_energy += delta
            accepted_moves += 1
            if current_energy < best_energy - 1.0e-12:
                best_energy = current_energy
                best_state = list(state)
        temperature = max(float(final_temperature), temperature*float(cooling_rate))
    refined_state, flips = (
        one_flip_descent(best_state, linear, adjacency)
        if run_local_refinement else (list(best_state), 0)
    )
    raw_solution = state_to_solution(variable_names, best_state)
    refined_solution = state_to_solution(variable_names, refined_state)
    raw_energy = calculate_qubo_energy(
        raw_solution, qubo["linear_terms"], qubo["quadratic_terms"]
    )
    refined_energy = calculate_qubo_energy(
        refined_solution, qubo["linear_terms"], qubo["quadratic_terms"]
    )
    return {
        "success": True, "status": "success", "error": None, "seed": seed,
        "raw_energy": raw_energy, "refined_energy": refined_energy,
        "raw_solution": raw_solution, "refined_solution": refined_solution,
        "accepted_moves": accepted_moves, "local_refinement_flips": flips,
        "runtime_seconds": round(time.perf_counter()-started, 6),
    }


def energy_decomposition(qubo: dict[str, Any], solution: dict[str, int]) -> dict[str, Any]:
    linear_reward = sum(
        float(coefficient) * int(solution.get(variable, 0))
        for variable, coefficient in qubo["linear_terms"].items()
    )
    quadratic = 0.0
    overlap = 0.0
    crossing = 0.0
    for term in qubo["quadratic_terms"]:
        contribution = (
            float(term["coefficient"])
            * int(solution.get(term["var_a"], 0))
            * int(solution.get(term["var_b"], 0))
        )
        quadratic += contribution
        reasons = set(term.get("reasons", []))
        if "overlap" in reasons and "crossing" in reasons:
            total_setting = (
                float(qubo["penalty_settings"]["overlap_penalty"])
                + float(qubo["penalty_settings"]["crossing_penalty"])
            )
            if total_setting:
                overlap += contribution * float(qubo["penalty_settings"]["overlap_penalty"])/total_setting
                crossing += contribution * float(qubo["penalty_settings"]["crossing_penalty"])/total_setting
        elif "overlap" in reasons:
            overlap += contribution
        elif "crossing" in reasons:
            crossing += contribution
    total = linear_reward + quadratic
    return {
        "total_energy": round(total, 6),
        "linear_reward": round(linear_reward, 6),
        "quadratic_penalty": round(quadratic, 6),
        "overlap_penalty_contribution": round(overlap, 6),
        "crossing_penalty_contribution": round(crossing, 6),
        "selected_variable_count": sum(int(value) for value in solution.values()),
    }


def _metric(reference: str | None, predicted: str | None) -> dict[str, Any] | None:
    if not reference or not predicted:
        return None
    try:
        return compare_structures(reference, predicted)
    except Exception:
        return None


def diagnose_sequence(
    exact_status: str,
    exact_f1: float | None,
    greedy_f1: float | None,
    best_f1: float | None,
    exact_energy: float | None,
    greedy_energy: float | None,
    best_energy: float | None,
    unique_structures: int,
    modal_frequency: float,
    tolerance: float,
) -> str:
    if exact_status == "success" and exact_energy is not None:
        if exact_f1 is not None and exact_f1 < 0.999999:
            return "objective_limitation_confirmed_small_qubo"
        solver_missed = any(
            value is not None and value > exact_energy + tolerance
            for value in (greedy_energy, best_energy)
        )
        if solver_missed:
            return "solver_limitation_confirmed_small_qubo"
        return "objective_and_solvers_agree_small_qubo"
    if best_f1 is not None and best_f1 >= 0.95:
        return "best_known_solution_matches_reference_large_qubo"
    if unique_structures > 1 or modal_frequency < 0.8:
        return "solver_instability_large_qubo"
    if best_f1 is not None and best_f1 < 0.5:
        return "likely_objective_limitation_large_qubo"
    return "ambiguous_large_qubo_requires_stronger_solver"


def _float_mean(values: list[float]) -> float | None:
    return round(statistics.fmean(values), 6) if values else None


def _float_std(values: list[float]) -> float | None:
    return round(statistics.pstdev(values), 6) if len(values) >= 2 else 0.0 if values else None


def _run_sequence(
    row: dict[str, str],
    strict: dict[str, Any],
    config: dict[str, Any],
    output_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    started = time.perf_counter()
    sequence = row["sequence"]
    sequence_id = row["sequence_id"]
    run_dir = output_dir / "runs" / sequence_id
    run_dir.mkdir(parents=True, exist_ok=True)

    vienna = run_rnafold(
        sequence,
        executable=str(strict.get("rnafold_executable", "RNAfold")),
        allow_python_fallback=bool(strict.get("allow_vienna_python_fallback", True)),
    )
    reference = vienna.get("reference_structure") if vienna.get("success") else None

    qubo = build_stem_qubo(
        sequence,
        overlap_penalty=float(strict.get("overlap_penalty", 14.0)),
        crossing_penalty=float(strict.get("crossing_penalty", 12.0)),
        min_stem_length=int(strict.get("stem_min_length", 2)),
        min_loop_length=int(strict.get("min_loop_length", 3)),
        allow_wobble=bool(strict.get("allow_wobble", True)),
    )
    exact = solve_stem_qubo_exact(
        sequence,
        max_variables=int(config.get("exact_max_variables", 20)),
        min_stem_length=int(strict.get("stem_min_length", 2)),
        min_loop_length=int(strict.get("min_loop_length", 3)),
        allow_wobble=bool(strict.get("allow_wobble", True)),
        overlap_penalty=float(strict.get("overlap_penalty", 14.0)),
        crossing_penalty=float(strict.get("crossing_penalty", 12.0)),
    )
    greedy = solve_stem_qubo_greedy(
        sequence,
        min_stem_length=int(strict.get("stem_min_length", 2)),
        min_loop_length=int(strict.get("min_loop_length", 3)),
        allow_wobble=bool(strict.get("allow_wobble", True)),
        overlap_penalty=float(strict.get("overlap_penalty", 14.0)),
        crossing_penalty=float(strict.get("crossing_penalty", 12.0)),
    )

    exact_metric = _metric(reference, exact.get("predicted_structure"))
    greedy_metric = _metric(reference, greedy.get("predicted_structure"))
    sa_rows: list[dict[str, Any]] = []
    decomp_rows: list[dict[str, Any]] = []
    successful_runs: list[dict[str, Any]] = []

    for seed in [int(value) for value in config["sa_seeds"]]:
        result = run_fast_sa(
            qubo,
            seed=seed,
            steps=int(config["sa_steps"]),
            initial_temperature=float(config["sa_initial_temperature"]),
            final_temperature=float(config["sa_final_temperature"]),
            cooling_rate=float(config["sa_cooling_rate"]),
            run_local_refinement=bool(config["run_local_refinement"]),
        )
        raw_decoded = decode_solution_to_structure(sequence, qubo["stems"], result["raw_solution"])
        refined_decoded = decode_solution_to_structure(sequence, qubo["stems"], result["refined_solution"])
        raw_metric = _metric(reference, raw_decoded.get("predicted_structure"))
        refined_metric = _metric(reference, refined_decoded.get("predicted_structure"))
        sa_row = {
            "sequence_id": sequence_id,
            "seed": seed,
            "status": result["status"],
            "error": result["error"],
            "raw_energy": result["raw_energy"],
            "refined_energy": result["refined_energy"],
            "raw_structure": raw_decoded.get("predicted_structure"),
            "refined_structure": refined_decoded.get("predicted_structure"),
            "raw_f1": raw_metric.get("f1_score") if raw_metric else None,
            "refined_f1": refined_metric.get("f1_score") if refined_metric else None,
            "accepted_moves": result["accepted_moves"],
            "local_refinement_flips": result["local_refinement_flips"],
            "selected_stem_count": refined_decoded.get("selected_stem_count"),
            "is_conflict_free": refined_decoded.get("is_conflict_free"),
            "runtime_seconds": result["runtime_seconds"],
        }
        sa_rows.append(sa_row)
        if refined_decoded.get("predicted_structure") is not None:
            full = dict(sa_row)
            full["solution"] = result["refined_solution"]
            full["metric"] = refined_metric
            full["decoded"] = refined_decoded
            successful_runs.append(full)
            decomposition = energy_decomposition(qubo, result["refined_solution"])
            decomp_rows.append({
                "sequence_id": sequence_id, "solver": "fast_sa_refined", "seed": seed,
                **decomposition,
                "recomputed_energy": calculate_qubo_energy(result["refined_solution"], qubo["linear_terms"], qubo["quadratic_terms"]),
                "is_conflict_free": refined_decoded.get("is_conflict_free"),
                "predicted_structure": refined_decoded.get("predicted_structure"),
            })

    for solver_name, result in (("exact", exact), ("greedy", greedy)):
        solution = result.get("best_solution") or {}
        decoded_structure = result.get("predicted_structure")
        if solution:
            decomposition = energy_decomposition(qubo, solution)
            decomp_rows.append({
                "sequence_id": sequence_id, "solver": solver_name, "seed": "",
                **decomposition,
                "recomputed_energy": calculate_qubo_energy(solution, qubo["linear_terms"], qubo["quadratic_terms"]),
                "is_conflict_free": result.get("is_conflict_free"),
                "predicted_structure": decoded_structure,
            })

    refined_energies = [float(run["refined_energy"]) for run in successful_runs]
    best_sa = min(successful_runs, key=lambda item: (float(item["refined_energy"]), int(item["seed"]))) if successful_runs else None
    structures = Counter(str(run["refined_structure"]) for run in successful_runs)
    modal_structure, modal_count = structures.most_common(1)[0] if structures else (None, 0)
    modal_frequency = modal_count/len(successful_runs) if successful_runs else 0.0
    best_sa_energy = float(best_sa["refined_energy"]) if best_sa else None
    best_sa_f1 = best_sa["metric"].get("f1_score") if best_sa and best_sa.get("metric") else None
    candidates = []
    if exact.get("status") == "success" and exact.get("best_energy") is not None and exact.get("predicted_structure"):
        candidates.append((float(exact["best_energy"]), "exact", exact.get("predicted_structure"), exact_metric))
    if greedy.get("best_energy") is not None and greedy.get("predicted_structure"):
        candidates.append((float(greedy["best_energy"]), "greedy", greedy.get("predicted_structure"), greedy_metric))
    if best_sa:
        candidates.append((float(best_sa["refined_energy"]), "sa", best_sa.get("refined_structure"), best_sa.get("metric")))
    best_known = min(candidates, key=lambda item: (item[0], {"exact":0,"sa":1,"greedy":2}.get(item[1],9))) if candidates else None
    tolerance = float(config["energy_tolerance"])
    best_hit_rate = (
        sum(abs(value-best_sa_energy) <= tolerance for value in refined_energies)/len(refined_energies)
        if refined_energies and best_sa_energy is not None else None
    )
    exact_energy = float(exact["best_energy"]) if exact.get("best_energy") is not None else None
    greedy_energy = float(greedy["best_energy"]) if greedy.get("best_energy") is not None else None
    diagnosis = diagnose_sequence(
        str(exact.get("status")),
        exact_metric.get("f1_score") if exact_metric else None,
        greedy_metric.get("f1_score") if greedy_metric else None,
        best_sa_f1,
        exact_energy,
        greedy_energy,
        best_sa_energy,
        len(structures),
        modal_frequency,
        tolerance,
    )
    summary = {
        "sequence_id": sequence_id, "split": row["split"], "category": row["category"],
        "sequence": sequence, "sequence_length": len(sequence), "status": "success",
        "error": None, "vienna_backend": vienna.get("backend"),
        "reference_structure": reference, "reference_energy": vienna.get("reference_energy"),
        "candidate_stem_count": len(qubo["stems"]), "qubo_variable_count": qubo["num_variables"],
        "quadratic_term_count": qubo["num_quadratic_terms"],
        "exact_status": exact.get("status"), "exact_energy": exact_energy,
        "exact_f1": exact_metric.get("f1_score") if exact_metric else None,
        "greedy_energy": greedy_energy, "greedy_f1": greedy_metric.get("f1_score") if greedy_metric else None,
        "sa_run_count": len(sa_rows), "sa_success_count": len(successful_runs),
        "sa_raw_best_energy": min(float(run["raw_energy"]) for run in successful_runs) if successful_runs else None,
        "sa_refined_best_energy": best_sa_energy,
        "sa_mean_refined_energy": _float_mean(refined_energies),
        "sa_worst_refined_energy": max(refined_energies) if refined_energies else None,
        "sa_energy_std": _float_std(refined_energies),
        "sa_unique_structure_count": len(structures), "sa_modal_structure": modal_structure,
        "sa_modal_structure_frequency": round(modal_frequency, 6),
        "sa_best_energy_hit_rate": round(best_hit_rate, 6) if best_hit_rate is not None else None,
        "sa_best_f1": best_sa_f1,
        "best_known_energy": best_known[0] if best_known else None,
        "best_known_structure": best_known[2] if best_known else None,
        "best_known_f1": best_known[3].get("f1_score") if best_known and best_known[3] else None,
        "greedy_energy_gap": round(greedy_energy-best_known[0], 6) if best_known and greedy_energy is not None else None,
        "exact_energy_gap": round(exact_energy-best_known[0], 6) if best_known and exact_energy is not None else None,
        "diagnosis": diagnosis,
        "runtime_seconds": round(time.perf_counter()-started, 6), "run_directory": str(run_dir),
    }
    frequency_rows = []
    for structure, count in structures.most_common():
        matching = [run for run in successful_runs if run["refined_structure"] == structure]
        energies = [float(run["refined_energy"]) for run in matching]
        f1_values = [float(run["refined_f1"]) for run in matching if run.get("refined_f1") is not None]
        frequency_rows.append({
            "sequence_id": sequence_id, "structure": structure, "count": count,
            "frequency": round(count/len(successful_runs), 6) if successful_runs else 0.0,
            "best_energy": min(energies) if energies else None,
            "mean_energy": _float_mean(energies), "best_f1": max(f1_values) if f1_values else None,
            "is_modal": structure == modal_structure,
        })
    detail = {"input": row, "vienna": vienna, "qubo_summary": {
        "variables": qubo["num_variables"], "quadratic_terms": qubo["num_quadratic_terms"],
        "penalty_settings": qubo["penalty_settings"], "candidate_settings": qubo["candidate_settings"],
    }, "exact": exact, "greedy": greedy, "sa_runs": sa_rows, "summary": summary}
    _write_json(run_dir/"diagnostic_detail.json", detail)
    return summary, sa_rows, frequency_rows, decomp_rows


def _report(summary: dict[str, Any], rows: list[dict[str, Any]], config: dict[str, Any], output_dir: Path) -> str:
    diagnosis_counts = Counter(str(row.get("diagnosis")) for row in rows if row.get("status") == "success")
    lines = [
        "# Phase 50A Solver Robustness Diagnostic Report", "",
        f"- Run ID: `{output_dir.name}`", f"- Output: `{output_dir}`",
        f"- Sequences: {summary['sequence_count']}",
        f"- Successful: {summary['successful_sequence_count']}",
        f"- Total SA runs: {summary['total_sa_runs']}",
        f"- Mean SA best-energy hit rate: {summary['mean_sa_best_energy_hit_rate']}",
        f"- Mean SA unique structures per sequence: {summary['mean_sa_unique_structure_count']}",
        f"- Mean best-known F1: {summary['mean_best_known_f1']}", "",
        "## Diagnostic counts", "",
    ]
    for key, value in sorted(diagnosis_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "", "## Interpretation boundary", "",
        "For QUBOs at or below the exact-variable limit, exact enumeration can separate objective failure from solver failure. For larger QUBOs, labels such as likely objective limitation or solver instability are diagnostic inferences, not proofs.",
        "", "## Frozen-data rule", "",
        "This phase uses a new development split. The Phase 49 held-out validation set is not used for tuning. The Phase 50 final_test split must remain unused until objective refinements are locked.",
        "", "## Reproducibility files", "",
        "- `dataset_snapshot.csv`", "- `effective_phase50_config.yaml`",
        "- `effective_strict_config.yaml`", "- `sequence_summary.csv`",
        "- `sa_runs.csv`", "- `structure_frequencies.csv`",
        "- `energy_decomposition.csv`", "- `diagnostic_summary.json`",
        "- `failed_runs.csv`", "", "## Configuration", "", "```json",
        json.dumps(config, indent=2, sort_keys=True, default=str), "```", "",
    ])
    return "\n".join(lines)


def run_diagnostics(
    split: str = "development",
    run_id: str | None = None,
    config_path: str | Path | None = None,
    sequence_limit: int | None = None,
    seed_limit: int | None = None,
    steps_override: int | None = None,
) -> dict[str, Any]:
    config = load_phase50_config(config_path)
    strict = load_strict_config(config["strict_config_path"])
    if seed_limit is not None:
        config["sa_seeds"] = list(config["sa_seeds"])[:seed_limit]
    if steps_override is not None:
        config["sa_steps"] = int(steps_override)
    dataset = load_dataset(config["dataset_path"], split)
    if sequence_limit is not None:
        dataset = dataset[:sequence_limit]
    safe_run_id = _safe_id(run_id, "phase50_diagnostics")
    output_dir = _resolve(config["output_root"])/safe_run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir/"dataset_snapshot.csv", dataset, ["sequence_id","split","category","source_type","notes","sequence"])
    _write_yaml(output_dir/"effective_phase50_config.yaml", config)
    _write_yaml(output_dir/"effective_strict_config.yaml", strict)

    sequence_rows: list[dict[str, Any]] = []
    sa_rows: list[dict[str, Any]] = []
    frequency_rows: list[dict[str, Any]] = []
    decomp_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(dataset, start=1):
        print(f"[{index}/{len(dataset)}] {row['sequence_id']} ({len(row['sequence'])} nt)")
        try:
            summary, sequence_sa, frequencies, decompositions = _run_sequence(row, strict, config, output_dir)
            sequence_rows.append(summary)
            sa_rows.extend(sequence_sa)
            frequency_rows.extend(frequencies)
            decomp_rows.extend(decompositions)
        except Exception as exc:
            failure = {"sequence_id": row["sequence_id"], "split": row["split"], "category": row["category"], "sequence": row["sequence"], "status": "failed", "error": f"{type(exc).__name__}: {exc}", "run_directory": str(output_dir/"runs"/row["sequence_id"])}
            sequence_rows.append(failure)
            failed_rows.append(failure)
            if config.get("fail_fast"):
                raise
    successful = [row for row in sequence_rows if row.get("status") == "success"]
    best_f1 = [float(row["best_known_f1"]) for row in successful if row.get("best_known_f1") is not None]
    hit_rates = [float(row["sa_best_energy_hit_rate"]) for row in successful if row.get("sa_best_energy_hit_rate") is not None]
    unique_counts = [float(row["sa_unique_structure_count"]) for row in successful if row.get("sa_unique_structure_count") is not None]
    diagnostic_summary = {
        "sequence_count": len(sequence_rows), "successful_sequence_count": len(successful),
        "failed_sequence_count": len(failed_rows),
        "success_rate": round(len(successful)/len(sequence_rows), 6) if sequence_rows else 0.0,
        "total_sa_runs": len(sa_rows),
        "mean_sa_best_energy_hit_rate": _float_mean(hit_rates),
        "mean_sa_unique_structure_count": _float_mean(unique_counts),
        "mean_best_known_f1": _float_mean(best_f1),
        "diagnosis_counts": dict(Counter(str(row.get("diagnosis")) for row in successful)),
        "phase49_validation_used": False,
        "split": split,
    }
    _write_csv(output_dir/"sequence_summary.csv", sequence_rows, SEQUENCE_FIELDS)
    _write_csv(output_dir/"sa_runs.csv", sa_rows, SA_FIELDS)
    _write_csv(output_dir/"structure_frequencies.csv", frequency_rows, FREQUENCY_FIELDS)
    _write_csv(output_dir/"energy_decomposition.csv", decomp_rows, DECOMPOSITION_FIELDS)
    _write_csv(output_dir/"failed_runs.csv", failed_rows, ["sequence_id","split","category","sequence","status","error","run_directory"])
    _write_json(output_dir/"diagnostic_summary.json", diagnostic_summary)
    (output_dir/"diagnostic_report.md").write_text(_report(diagnostic_summary, sequence_rows, config, output_dir), encoding="utf-8")
    print(f"[OK] Phase 50A diagnostics saved to: {output_dir}")
    print(f"[OK] Successful sequences: {len(successful)}/{len(sequence_rows)}")
    print(f"[OK] Total SA runs: {len(sa_rows)}")
    return {"output_dir": str(output_dir), "summary": diagnostic_summary, "sequence_rows": sequence_rows}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Phase 50A multi-seed solver diagnostics.")
    parser.add_argument("--split", default="development", choices=["development", "final_test"])
    parser.add_argument("--run-id")
    parser.add_argument("--config", default="configs/phase50_solver_diagnostics.yaml")
    parser.add_argument("--sequence-limit", type=int)
    parser.add_argument("--seed-limit", type=int)
    parser.add_argument("--steps", type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        run_diagnostics(args.split, args.run_id, args.config, args.sequence_limit, args.seed_limit, args.steps)
        return 0
    except Exception as exc:
        print(f"[ERROR] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
