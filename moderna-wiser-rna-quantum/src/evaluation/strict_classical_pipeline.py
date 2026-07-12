from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.classical.dotbracket_tools import pairs_to_dotbracket
from src.classical.vienna_rnafold import run_rnafold, validate_rna_sequence
from src.evaluation.energy_comparison import compare_energy
from src.evaluation.experiment_report_writer import save_experiment_outputs
from src.evaluation.runtime_summary import RuntimeTracker
from src.evaluation.structural_comparison import compare_structures

BasePair = Tuple[int, int]
QuboKey = Tuple[int, int]


DEFAULT_CONFIG: Dict[str, Any] = {
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
}


def load_config(config_path: Optional[str]) -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    if config_path:
        if yaml is None:
            raise RuntimeError("PyYAML is required to read YAML config files. Run: python -m pip install pyyaml")
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError("Config file must contain a YAML mapping.")
        config.update(loaded)
    return config


def can_pair(left: str, right: str, allow_wobble: bool = True) -> bool:
    pair = (left.upper(), right.upper())
    canonical = {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G")}
    wobble = {("G", "U"), ("U", "G")}
    return pair in canonical or (allow_wobble and pair in wobble)


def pair_type(left: str, right: str) -> str:
    pair = (left.upper(), right.upper())
    if pair in {("A", "U"), ("U", "A")}: 
        return "AU"
    if pair in {("G", "C"), ("C", "G")}: 
        return "GC"
    if pair in {("G", "U"), ("U", "G")}: 
        return "GU"
    return "invalid"


def pair_score(pair_kind: str) -> float:
    if pair_kind == "GC":
        return 3.0
    if pair_kind == "AU":
        return 2.0
    if pair_kind == "GU":
        return 1.0
    return 0.0


def generate_candidate_pairs(sequence: str, min_loop_length: int, allow_wobble: bool) -> List[Dict[str, Any]]:
    cleaned = validate_rna_sequence(sequence)
    pairs: List[Dict[str, Any]] = []
    for i in range(len(cleaned)):
        for j in range(i + min_loop_length + 1, len(cleaned)):
            if can_pair(cleaned[i], cleaned[j], allow_wobble=allow_wobble):
                kind = pair_type(cleaned[i], cleaned[j])
                pairs.append({
                    "pair_id": len(pairs),
                    "i": i,
                    "j": j,
                    "left_base": cleaned[i],
                    "right_base": cleaned[j],
                    "pair_type": kind,
                    "score": pair_score(kind),
                })
    return pairs


def generate_candidate_stems(candidate_pairs: List[Dict[str, Any]], stem_min_length: int) -> List[Dict[str, Any]]:
    pair_lookup = {(int(row["i"]), int(row["j"])): row for row in candidate_pairs}
    stems: List[Dict[str, Any]] = []
    seen: set[Tuple[Tuple[int, int], ...]] = set()

    for row in candidate_pairs:
        start_i = int(row["i"])
        start_j = int(row["j"])
        chain: List[BasePair] = []
        k = 0
        while (start_i + k, start_j - k) in pair_lookup and start_i + k < start_j - k:
            chain.append((start_i + k, start_j - k))
            k += 1
        if len(chain) >= stem_min_length:
            stem_pairs = tuple(chain)
            if stem_pairs not in seen:
                seen.add(stem_pairs)
                score = sum(float(pair_lookup[p]["score"]) for p in stem_pairs)
                stems.append({
                    "stem_id": len(stems),
                    "pairs": list(stem_pairs),
                    "start_i": stem_pairs[0][0],
                    "start_j": stem_pairs[0][1],
                    "length": len(stem_pairs),
                    "score": score,
                })

    if not stems:
        for row in candidate_pairs:
            pair = (int(row["i"]), int(row["j"]))
            stems.append({
                "stem_id": len(stems),
                "pairs": [pair],
                "start_i": pair[0],
                "start_j": pair[1],
                "length": 1,
                "score": float(row["score"]),
            })
    return stems


def stem_positions(stem: Dict[str, Any]) -> set[int]:
    positions: set[int] = set()
    for left, right in stem["pairs"]:
        positions.add(int(left))
        positions.add(int(right))
    return positions


def pairs_cross(pair_a: BasePair, pair_b: BasePair) -> bool:
    a, b = pair_a
    c, d = pair_b
    return (a < c < b < d) or (c < a < d < b)


def stems_overlap(stem_a: Dict[str, Any], stem_b: Dict[str, Any]) -> bool:
    return bool(stem_positions(stem_a).intersection(stem_positions(stem_b)))


def stems_cross(stem_a: Dict[str, Any], stem_b: Dict[str, Any]) -> bool:
    for pair_a in stem_a["pairs"]:
        for pair_b in stem_b["pairs"]:
            if pairs_cross((int(pair_a[0]), int(pair_a[1])), (int(pair_b[0]), int(pair_b[1]))):
                return True
    return False


def build_stem_qubo(
    stems: List[Dict[str, Any]],
    overlap_penalty: float,
    crossing_penalty: float,
) -> tuple[Dict[QuboKey, float], List[Dict[str, Any]]]:
    qubo: Dict[QuboKey, float] = {}
    summary: List[Dict[str, Any]] = []

    for idx, stem in enumerate(stems):
        value = -float(stem["score"])
        qubo[(idx, idx)] = value
        summary.append({
            "term_type": "linear",
            "var_i": idx,
            "var_j": idx,
            "coefficient": value,
            "reason": "negative reward for selecting a candidate stem",
        })

    for i, j in itertools.combinations(range(len(stems)), 2):
        coefficient = 0.0
        reasons = []
        if stems_overlap(stems[i], stems[j]):
            coefficient += float(overlap_penalty)
            reasons.append("overlap")
        if stems_cross(stems[i], stems[j]):
            coefficient += float(crossing_penalty)
            reasons.append("crossing")
        if coefficient != 0.0:
            qubo[(i, j)] = coefficient
            summary.append({
                "term_type": "quadratic",
                "var_i": i,
                "var_j": j,
                "coefficient": coefficient,
                "reason": "+".join(reasons),
            })
    return qubo, summary


def qubo_energy(bitstring: List[int], qubo: Dict[QuboKey, float]) -> float:
    energy = 0.0
    for (i, j), coefficient in qubo.items():
        energy += coefficient * bitstring[i] * bitstring[j]
    return float(energy)


def exact_solve(qubo: Dict[QuboKey, float], variable_count: int, max_variables: int) -> Optional[Dict[str, Any]]:
    if variable_count > max_variables:
        return None
    best_bits: Optional[List[int]] = None
    best_energy = float("inf")
    for bits in itertools.product([0, 1], repeat=variable_count):
        bit_list = list(bits)
        energy = qubo_energy(bit_list, qubo)
        if energy < best_energy:
            best_energy = energy
            best_bits = bit_list
    return {"solver": "exact", "bitstring": best_bits or [], "energy": best_energy}


def greedy_solve(stems: List[Dict[str, Any]], qubo: Dict[QuboKey, float]) -> Dict[str, Any]:
    bitstring = [0] * len(stems)
    for idx, _stem in sorted(enumerate(stems), key=lambda item: float(item[1]["score"]), reverse=True):
        candidate = bitstring.copy()
        candidate[idx] = 1
        if qubo_energy(candidate, qubo) <= qubo_energy(bitstring, qubo):
            bitstring = candidate
    return {"solver": "greedy", "bitstring": bitstring, "energy": qubo_energy(bitstring, qubo)}


def simulated_annealing_solve(
    qubo: Dict[QuboKey, float],
    variable_count: int,
    steps: int,
    initial_temperature: float,
    final_temperature: float,
    cooling_rate: float,
    random_seed: int,
) -> Dict[str, Any]:
    rng = random.Random(random_seed)
    bitstring = [rng.randint(0, 1) for _ in range(variable_count)]
    current_energy = qubo_energy(bitstring, qubo)
    best_bits = bitstring.copy()
    best_energy = current_energy
    temperature = max(float(initial_temperature), 1e-12)

    for _ in range(max(1, int(steps))):
        idx = rng.randrange(variable_count) if variable_count else 0
        candidate = bitstring.copy()
        if variable_count:
            candidate[idx] = 1 - candidate[idx]
        candidate_energy = qubo_energy(candidate, qubo)
        delta = candidate_energy - current_energy
        accept = delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-12))
        if accept:
            bitstring = candidate
            current_energy = candidate_energy
            if current_energy < best_energy:
                best_bits = bitstring.copy()
                best_energy = current_energy
        temperature = max(float(final_temperature), temperature * float(cooling_rate))
    return {"solver": "simulated_annealing", "bitstring": best_bits, "energy": best_energy}


def decode_bitstring(bitstring: List[int], stems: List[Dict[str, Any]]) -> List[BasePair]:
    selected_pairs: List[BasePair] = []
    used_positions: set[int] = set()
    for selected, stem in zip(bitstring, stems):
        if not selected:
            continue
        for left, right in stem["pairs"]:
            left_i = int(left)
            right_i = int(right)
            if left_i not in used_positions and right_i not in used_positions:
                selected_pairs.append((left_i, right_i))
                used_positions.add(left_i)
                used_positions.add(right_i)
    return sorted(selected_pairs)


def choose_best_solver_result(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {"solver": "none", "bitstring": [], "energy": None}
    return min(results, key=lambda row: float("inf") if row.get("energy") is None else float(row["energy"]))


def serialize_stems(stems: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for stem in stems:
        rows.append({
            "stem_id": stem["stem_id"],
            "pairs": json.dumps(stem["pairs"]),
            "start_i": stem["start_i"],
            "start_j": stem["start_j"],
            "length": stem["length"],
            "score": stem["score"],
        })
    return rows


def run_pipeline(sequence: str, run_id: str, config: Dict[str, Any], output_root: str = "results/classical_foundation") -> Dict[str, Any]:
    tracker = RuntimeTracker()
    cleaned_sequence = validate_rna_sequence(sequence)

    tracker.start("vienna_rnafold")
    vienna_reference = run_rnafold(
        cleaned_sequence,
        timeout_seconds=int(config.get("rnafold_timeout_seconds", 15)),
        executable=str(config.get("rnafold_executable", "RNAfold")),
        allow_python_fallback=bool(config.get("allow_vienna_python_fallback", True)),
    )
    tracker.stop()

    tracker.start("candidate_pair_generation")
    candidate_pairs = generate_candidate_pairs(
        cleaned_sequence,
        min_loop_length=int(config["min_loop_length"]),
        allow_wobble=bool(config["allow_wobble"]),
    )
    tracker.stop()

    tracker.start("candidate_stem_generation")
    candidate_stems = generate_candidate_stems(candidate_pairs, int(config["stem_min_length"]))
    tracker.stop()

    tracker.start("qubo_build")
    qubo, qubo_summary = build_stem_qubo(
        candidate_stems,
        overlap_penalty=float(config["overlap_penalty"]),
        crossing_penalty=float(config["crossing_penalty"]),
    )
    tracker.stop()

    solver_results: List[Dict[str, Any]] = []
    tracker.start("solver_execution")
    exact_result = exact_solve(qubo, len(candidate_stems), int(config["solver_exact_max_variables"]))
    if exact_result is not None:
        solver_results.append(exact_result)
    if bool(config.get("run_greedy", True)):
        solver_results.append(greedy_solve(candidate_stems, qubo))
    if bool(config.get("run_simulated_annealing", True)):
        solver_results.append(simulated_annealing_solve(
            qubo=qubo,
            variable_count=len(candidate_stems),
            steps=int(config["simulated_annealing_steps"]),
            initial_temperature=float(config["simulated_annealing_initial_temperature"]),
            final_temperature=float(config["simulated_annealing_final_temperature"]),
            cooling_rate=float(config["simulated_annealing_cooling_rate"]),
            random_seed=int(config["random_seed"]),
        ))
    tracker.stop()

    best = choose_best_solver_result(solver_results)
    predicted_pairs = decode_bitstring(best["bitstring"], candidate_stems)
    predicted_dotbracket = pairs_to_dotbracket(len(cleaned_sequence), predicted_pairs)
    predicted_structure = {
        "predicted_dotbracket": predicted_dotbracket,
        "predicted_pairs": predicted_pairs,
        "solver": best["solver"],
        "qubo_energy": best["energy"],
        "selected_bitstring": best["bitstring"],
        "candidate_stem_count": len(candidate_stems),
        "candidate_pair_count": len(candidate_pairs),
    }

    reference_structure = vienna_reference.get("reference_structure")
    if isinstance(reference_structure, str) and len(reference_structure) == len(predicted_dotbracket):
        structural_comparison = compare_structures(reference_structure, predicted_dotbracket)
        structural_comparison["comparison_available"] = True
    else:
        structural_comparison = {
            "comparison_available": False,
            "reason": vienna_reference.get("error") or "ViennaRNA reference structure unavailable.",
            "reference_dotbracket": reference_structure,
            "predicted_dotbracket": predicted_dotbracket,
            "exact_match": None,
            "precision": None,
            "recall": None,
            "f1_score": None,
            "base_pair_distance": None,
        }

    energy_comparison = compare_energy(vienna_reference.get("reference_energy"), best.get("energy"))
    runtime_summary = tracker.summary()
    output_dir = Path(output_root) / run_id

    saved_paths = save_experiment_outputs(
        output_dir=output_dir,
        run_id=run_id,
        sequence=cleaned_sequence,
        vienna_reference=vienna_reference,
        candidate_pairs=candidate_pairs,
        candidate_stems=serialize_stems(candidate_stems),
        qubo_summary=qubo_summary,
        solver_results=[{
            "solver": row["solver"],
            "energy": row["energy"],
            "bitstring": json.dumps(row["bitstring"]),
        } for row in solver_results],
        predicted_structure=predicted_structure,
        structural_comparison=structural_comparison,
        energy_comparison=energy_comparison,
        runtime_summary=runtime_summary,
        config=config,
    )

    return {
        "success": True,
        "run_id": run_id,
        "sequence": cleaned_sequence,
        "output_dir": str(output_dir),
        "vienna_success": vienna_reference.get("success"),
        "vienna_method": vienna_reference.get("vienna_method"),
        "vienna_structure": vienna_reference.get("reference_structure"),
        "vienna_energy": vienna_reference.get("reference_energy"),
        "predicted_dotbracket": predicted_dotbracket,
        "best_solver": best["solver"],
        "best_qubo_energy": best["energy"],
        "candidate_pair_count": len(candidate_pairs),
        "candidate_stem_count": len(candidate_stems),
        "structural_comparison_available": structural_comparison.get("comparison_available"),
        "energy_comparison_available": energy_comparison.get("comparison_available"),
        "saved_paths": saved_paths,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the strict classical RNA-QUBO foundation pipeline.")
    parser.add_argument("--sequence", default=None)
    parser.add_argument("--run-id", default=f"strict_classical_{int(time.time())}")
    parser.add_argument("--config", default="configs/strict_classical_foundation.yaml")
    parser.add_argument("--output-root", default="results/classical_foundation")
    args = parser.parse_args()

    config = load_config(args.config)
    sequence = args.sequence or str(config["sequence"])
    result = run_pipeline(sequence=sequence, run_id=args.run_id, config=config, output_root=args.output_root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
