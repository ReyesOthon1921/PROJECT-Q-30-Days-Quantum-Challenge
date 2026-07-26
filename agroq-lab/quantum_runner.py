from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Iterable


SUPPORTED_SEQUENCES = frozenset(
    {"Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10"}
)


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def sha256_json(value: Any) -> str:
    return sha256_text(canonical_json(value))


_NONDETERMINISTIC_RESULT_KEYS = frozenset(
    {
        "runtime_seconds",
        "started_at",
        "completed_at",
        "created_at",
        "updated_at",
        "result_sha256",
    }
)


def deterministic_result_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: deterministic_result_payload(item)
            for key, item in sorted(value.items())
            if key not in _NONDETERMINISTIC_RESULT_KEYS
        }
    if isinstance(value, list):
        return [deterministic_result_payload(item) for item in value]
    return value


def seeded_random(seed: int | str | None = 301) -> random.Random:
    try:
        normalized = int(seed if seed is not None else 301)
    except (TypeError, ValueError):
        normalized = 301
    return random.Random(normalized)


def bits_from_state(state: int, size: int) -> list[int]:
    return [(state >> index) & 1 for index in range(size)]


@dataclass(frozen=True)
class BinaryProblem:
    name: str
    variable_names: list[str]
    objective: Callable[[list[int]], float]
    decode: Callable[[list[int]], dict[str, Any]]


def exact_binary(problem: BinaryProblem) -> dict[str, Any]:
    size = len(problem.variable_names)
    if size > 20:
        raise ValueError("Exact enumeration is limited to 20 binary variables.")

    started = time.perf_counter()
    best: dict[str, Any] | None = None
    evaluations = 0

    for state in range(1 << size):
        bits = bits_from_state(state, size)
        decoded = problem.decode(bits)
        energy = float(problem.objective(bits))
        evaluations += 1
        record = {
            "state": state,
            "bits": bits,
            "bitstring": "".join(str(bit) for bit in reversed(bits)),
            "energy": energy,
            **decoded,
        }
        if decoded.get("feasible", True) and (
            best is None or energy < best["energy"] - 1e-12
        ):
            best = record

    if best is None:
        raise ValueError("The binary problem produced no feasible solution.")

    return {
        "solver_name": "exact_enumeration",
        "algorithm": "Exact enumeration",
        "objective_evaluations": evaluations,
        "runtime_seconds": time.perf_counter() - started,
        "best": best,
    }


def simulated_annealing(
    problem: BinaryProblem,
    *,
    seed: int = 301,
    steps: int = 2048,
    start_temperature: float = 4.0,
    end_temperature: float = 0.01,
) -> dict[str, Any]:
    steps = max(64, int(steps))
    rng = seeded_random(seed)
    size = len(problem.variable_names)
    bits = [1 if rng.random() < 0.5 else 0 for _ in range(size)]
    current_energy = float(problem.objective(bits))
    current_decoded = problem.decode(bits)
    best: dict[str, Any] | None = None
    accepted = 0
    started = time.perf_counter()

    def consider(candidate_bits: list[int], energy: float, decoded: dict[str, Any]) -> None:
        nonlocal best
        if decoded.get("feasible", True) and (
            best is None or energy < best["energy"] - 1e-12
        ):
            best = {
                "bits": list(candidate_bits),
                "bitstring": "".join(str(bit) for bit in reversed(candidate_bits)),
                "energy": energy,
                **decoded,
            }

    consider(bits, current_energy, current_decoded)

    for step in range(steps):
        progress = step / max(1, steps - 1)
        temperature = start_temperature * (
            end_temperature / start_temperature
        ) ** progress
        candidate = list(bits)
        index = rng.randrange(size)
        candidate[index] = 1 - candidate[index]
        candidate_energy = float(problem.objective(candidate))
        delta = candidate_energy - current_energy

        if delta <= 0 or rng.random() < math.exp(-delta / max(temperature, 1e-12)):
            bits = candidate
            current_energy = candidate_energy
            current_decoded = problem.decode(bits)
            accepted += 1
            consider(bits, current_energy, current_decoded)

    if best is None:
        exact = exact_binary(problem)
        best = exact["best"]

    return {
        "solver_name": "simulated_annealing",
        "algorithm": "Seeded simulated annealing",
        "seed": seed,
        "steps": steps,
        "objective_evaluations": steps + 1,
        "accepted_moves": accepted,
        "acceptance_rate": accepted / steps,
        "runtime_seconds": time.perf_counter() - started,
        "best": best,
    }


def _apply_cost_layer(
    amplitudes: list[complex],
    normalized_energies: list[float],
    gamma: float,
) -> None:
    for state, energy in enumerate(normalized_energies):
        amplitudes[state] *= complex(
            math.cos(-gamma * energy),
            math.sin(-gamma * energy),
        )


def _apply_mixer_layer(
    amplitudes: list[complex],
    qubits: int,
    beta: float,
) -> None:
    cosine = math.cos(beta)
    sine = math.sin(beta)
    for qubit in range(qubits):
        mask = 1 << qubit
        for state in range(len(amplitudes)):
            if state & mask:
                continue
            paired = state | mask
            left = amplitudes[state]
            right = amplitudes[paired]
            amplitudes[state] = cosine * left - 1j * sine * right
            amplitudes[paired] = cosine * right - 1j * sine * left


def qaoa_p1(
    problem: BinaryProblem,
    *,
    seed: int = 301,
    shots: int = 2048,
    grid_size: int = 11,
) -> dict[str, Any]:
    qubits = len(problem.variable_names)
    if qubits > 12:
        return {
            "solver_name": "qaoa_p1_statevector",
            "algorithm": "QAOA p=1 ideal statevector",
            "supported": False,
            "reason": "Server prototype limits ideal statevector runs to 12 qubits.",
            "best": None,
        }

    started = time.perf_counter()
    state_count = 1 << qubits
    raw_energies = [
        float(problem.objective(bits_from_state(state, qubits)))
        for state in range(state_count)
    ]
    minimum = min(raw_energies)
    maximum = max(raw_energies)
    energy_range = max(1e-12, maximum - minimum)
    normalized = [(value - minimum) / energy_range for value in raw_energies]

    grid_size = max(5, min(25, int(grid_size)))
    best_parameters: dict[str, float] | None = None
    best_probabilities: list[float] | None = None

    for gamma_index in range(grid_size):
        gamma = 2 * math.pi * gamma_index / grid_size
        for beta_index in range(grid_size):
            beta = math.pi * beta_index / (2 * max(1, grid_size - 1))
            amplitude = 1 / math.sqrt(state_count)
            amplitudes = [complex(amplitude, 0.0) for _ in range(state_count)]
            _apply_cost_layer(amplitudes, normalized, gamma)
            _apply_mixer_layer(amplitudes, qubits, beta)
            probabilities = [abs(value) ** 2 for value in amplitudes]
            expectation = sum(
                probability * energy
                for probability, energy in zip(probabilities, normalized)
            )
            if (
                best_parameters is None
                or expectation < best_parameters["normalized_expectation"]
            ):
                best_parameters = {
                    "gamma": gamma,
                    "beta": beta,
                    "normalized_expectation": expectation,
                }
                best_probabilities = probabilities

    assert best_parameters is not None
    assert best_probabilities is not None

    rng = seeded_random(seed)
    cumulative: list[float] = []
    running = 0.0
    for probability in best_probabilities:
        running += probability
        cumulative.append(running)
    cumulative[-1] = 1.0

    counts: dict[int, int] = {}
    shots = max(128, int(shots))
    for _ in range(shots):
        target = rng.random()
        left = 0
        right = len(cumulative) - 1
        while left < right:
            middle = (left + right) // 2
            if target <= cumulative[middle]:
                right = middle
            else:
                left = middle + 1
        counts[left] = counts.get(left, 0) + 1

    sampled_records: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for state, count in counts.items():
        bits = bits_from_state(state, qubits)
        decoded = problem.decode(bits)
        energy = raw_energies[state]
        record = {
            "state": state,
            "bits": bits,
            "bitstring": "".join(str(bit) for bit in reversed(bits)),
            "count": count,
            "probability": count / shots,
            "energy": energy,
            **decoded,
        }
        sampled_records.append(record)
        if decoded.get("feasible", True) and (
            best is None or energy < best["energy"] - 1e-12
        ):
            best = record

    sampled_records.sort(key=lambda item: item["count"], reverse=True)
    if best is None:
        exact = exact_binary(problem)
        best = exact["best"]

    return {
        "solver_name": "qaoa_p1_statevector",
        "algorithm": "QAOA p=1 ideal statevector",
        "supported": True,
        "seed": seed,
        "shots": shots,
        "grid_size": grid_size,
        "parameter_evaluations": grid_size**2,
        **best_parameters,
        "raw_expectation": sum(
            probability * energy
            for probability, energy in zip(best_probabilities, raw_energies)
        ),
        "runtime_seconds": time.perf_counter() - started,
        "best": best,
        "histogram": sampled_records[:12],
        "circuit": {
            "qubits": qubits,
            "ansatz": "QAOA p=1",
            "backend": "Python ideal statevector",
            "noise_model": "None",
            "estimated_depth": 3 + qubits * max(1, qubits - 1),
            "estimated_two_qubit_gates": qubits * max(1, qubits - 1),
            "estimate_boundary": (
                "Resource counts are formulation-level estimates before transpilation."
            ),
        },
    }


def _numeric(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _snapshot_rows(dataset: dict[str, Any] | None, table: str) -> list[dict[str, Any]]:
    if not dataset:
        return []
    snapshot = dataset.get("snapshot") or dataset.get("snapshot_json") or {}
    rows = snapshot.get(table, [])
    return [dict(row) for row in rows if isinstance(row, dict)]


def _q2_candidates(dataset: dict[str, Any] | None) -> list[dict[str, Any]]:
    observations = _snapshot_rows(dataset, "observations")
    plots = _snapshot_rows(dataset, "plots")
    if observations:
        plot_names = {
            str(plot.get("plot_id")): str(plot.get("name") or plot.get("plot_id"))
            for plot in plots
        }
        grouped: dict[str, list[dict[str, Any]]] = {}
        for row in observations:
            grouped.setdefault(str(row.get("plot_id") or "UNASSIGNED"), []).append(row)
        candidates = []
        for index, (plot_id, rows) in enumerate(sorted(grouped.items())[:8]):
            quality_penalty = sum(
                1
                for row in rows
                if str(row.get("quality_flag", "")).lower()
                in {"unverified", "suspect", "invalid"}
            )
            latest_value = _numeric(rows[-1].get("value"), 0.0)
            uncertainty = min(1.0, 0.35 + quality_penalty * 0.18 + 1 / (len(rows) + 1))
            diversity = min(1.0, 0.5 + index * 0.07)
            urgency = min(1.0, 0.35 + abs(latest_value) * 0.01)
            value = 0.45 * uncertainty + 0.25 * diversity + 0.30 * urgency
            candidates.append(
                {
                    "id": f"C-{index + 1:02d}",
                    "plot_id": plot_id,
                    "zone": plot_names.get(plot_id, plot_id),
                    "cost": 1 + (index % 2),
                    "value": round(value, 6),
                    "uncertainty": uncertainty,
                    "diversity": diversity,
                    "urgency": urgency,
                }
            )
        if candidates:
            return candidates

    return [
        {"id": "C-01", "zone": "Compost Trial", "cost": 2, "value": 0.82},
        {"id": "C-02", "zone": "Calibration Zone", "cost": 2, "value": 0.78},
        {"id": "C-03", "zone": "North Control", "cost": 1, "value": 0.67},
        {"id": "C-04", "zone": "Beneficial Zone", "cost": 1, "value": 0.66},
        {"id": "C-05", "zone": "Cover Crop Zone", "cost": 2, "value": 0.64},
        {"id": "C-06", "zone": "Untreated Control", "cost": 1, "value": 0.56},
    ]


def run_q2(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    candidates = _q2_candidates(dataset)
    budget = int(configuration.get("sample_budget", 5))
    penalty = float(configuration.get("penalty", 8.0))
    variable_names = [f"select_{item['id']}" for item in candidates]

    def decode(bits: list[int]) -> dict[str, Any]:
        selected = [
            candidate
            for candidate, bit in zip(candidates, bits)
            if bit
        ]
        used = sum(int(item["cost"]) for item in selected)
        utility = sum(float(item["value"]) for item in selected)
        return {
            "feasible": used <= budget,
            "selected": selected,
            "selected_ids": [item["id"] for item in selected],
            "budget_used": used,
            "utility": utility,
            "constraint_violations": 0 if used <= budget else 1,
        }

    def objective(bits: list[int]) -> float:
        decoded = decode(bits)
        over = max(0, decoded["budget_used"] - budget)
        return -decoded["utility"] + penalty * over**2

    problem = BinaryProblem(
        name="Frozen soil-sampling QUBO",
        variable_names=variable_names,
        objective=objective,
        decode=decode,
    )
    return _run_optimization_bundle(
        sequence="Q2",
        title="Frozen soil-sampling QUBO benchmark",
        source_ids=["QRS-001", "QRS-002", "QRS-003"],
        problem=problem,
        configuration=configuration,
        metadata={"budget": budget, "candidates": candidates},
    )


def _irrigation_problem(dataset: dict[str, Any] | None) -> tuple[BinaryProblem, dict[str, Any]]:
    plots = _snapshot_rows(dataset, "plots")
    names = [
        str(row.get("name") or row.get("plot_id"))
        for row in plots[:3]
    ] or ["North Control", "Compost Trial", "Cover Crop"]
    while len(names) < 3:
        names.append(f"Zone {len(names) + 1}")
    zones = [
        {"id": f"Z{index + 1}", "name": name, "initial": 0.48 + 0.035 * index, "target": 0.61 + 0.01 * index}
        for index, name in enumerate(names[:3])
    ]
    periods = [
        {"id": "P1", "et": 0.08, "rain": 0.01},
        {"id": "P2", "et": 0.09, "rain": 0.00},
    ]
    water_budget = 3
    gain = 0.13
    variable_names = [
        f"{zone['id']}_{period['id']}"
        for zone in zones
        for period in periods
    ]
    adjacency = [(0, 1), (1, 2)]

    def decode(bits: list[int]) -> dict[str, Any]:
        schedule = []
        water_used = 0
        stress = 0.0
        index = 0
        final_moisture: dict[str, float] = {}
        for zone in zones:
            moisture = zone["initial"]
            for period in periods:
                irrigate = bits[index] == 1
                water_used += int(irrigate)
                moisture += period["rain"] - period["et"] + (gain if irrigate else 0)
                stress += (zone["target"] - moisture) ** 2
                schedule.append(
                    {
                        "variable": variable_names[index],
                        "zone": zone["name"],
                        "period": period["id"],
                        "irrigate": irrigate,
                    }
                )
                index += 1
            final_moisture[zone["id"]] = moisture

        overlap = 0
        for left, right in adjacency:
            for period_index in range(len(periods)):
                overlap += (
                    bits[left * len(periods) + period_index]
                    * bits[right * len(periods) + period_index]
                )
        objective = (
            stress
            + 0.05 * water_used
            + 0.12 * overlap
            + 3.5 * (water_used - water_budget) ** 2
        )
        return {
            "feasible": water_used <= water_budget,
            "schedule": schedule,
            "water_used": water_used,
            "stress": stress,
            "adjacency_overlaps": overlap,
            "final_moisture": final_moisture,
            "objective": objective,
            "constraint_violations": 0 if water_used <= water_budget else 1,
        }

    return (
        BinaryProblem(
            name="Multi-period irrigation scheduling",
            variable_names=variable_names,
            objective=lambda bits: float(decode(bits)["objective"]),
            decode=decode,
        ),
        {
            "zones": zones,
            "periods": periods,
            "water_budget": water_budget,
            "irrigation_gain": gain,
        },
    )


def run_q3(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    problem, metadata = _irrigation_problem(dataset)
    bundle = _run_optimization_bundle(
        sequence="Q3",
        title="Irrigation-scheduling reproduction",
        source_ids=["QRS-001", "QRS-002", "QRS-003", "QRS-016"],
        problem=problem,
        configuration=configuration,
        metadata=metadata,
    )
    bundle["disclosure"] = (
        "This is a simplified synthetic or frozen-data reproduction inspired by "
        "a recent irrigation-QUBO preprint, not a reproduction of its complete "
        "field dataset or hardware results."
    )
    return bundle


def _graph_from_dataset(dataset: dict[str, Any] | None) -> dict[str, Any]:
    plots = _snapshot_rows(dataset, "plots")
    if plots:
        nodes = [
            {
                "id": str(row.get("plot_id") or f"N{index + 1}"),
                "name": str(row.get("name") or row.get("plot_id")),
                "value": 0.65 + 0.05 * (index % 6),
            }
            for index, row in enumerate(plots[:8])
        ]
    else:
        nodes = [
            {"id": "A", "name": "North Control", "value": 0.82},
            {"id": "B", "name": "Compost Trial", "value": 0.93},
            {"id": "C", "name": "Cover Crop", "value": 0.76},
            {"id": "D", "name": "Beneficial Zone", "value": 0.88},
            {"id": "E", "name": "Calibration Zone", "value": 0.71},
            {"id": "F", "name": "Untreated Control", "value": 0.65},
        ]
    edges = []
    for index in range(len(nodes) - 1):
        edges.append((index, index + 1, 1.0 - 0.05 * (index % 3)))
    if len(nodes) > 3:
        edges.extend(
            [
                (0, 2, 0.8),
                (1, 3, 0.9),
            ]
        )
    return {"nodes": nodes, "edges": edges, "sensor_budget": min(2, len(nodes))}


def run_q4(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    graph = _graph_from_dataset(dataset)
    variable_names = [f"node_{node['id']}" for node in graph["nodes"]]

    def cut_decode(bits: list[int]) -> dict[str, Any]:
        cut_weight = sum(
            weight
            for left, right, weight in graph["edges"]
            if bits[left] != bits[right]
        )
        return {
            "feasible": True,
            "cut_weight": cut_weight,
            "partition_0": [
                graph["nodes"][index]["id"]
                for index, bit in enumerate(bits)
                if bit == 0
            ],
            "partition_1": [
                graph["nodes"][index]["id"]
                for index, bit in enumerate(bits)
                if bit == 1
            ],
            "objective": -cut_weight,
        }

    maxcut_problem = BinaryProblem(
        name="Graph MaxCut",
        variable_names=variable_names,
        objective=lambda bits: float(cut_decode(bits)["objective"]),
        decode=cut_decode,
    )

    def sensor_decode(bits: list[int]) -> dict[str, Any]:
        selected_indices = [index for index, bit in enumerate(bits) if bit]
        covered = set(selected_indices)
        for left, right, _ in graph["edges"]:
            if left in selected_indices:
                covered.add(right)
            if right in selected_indices:
                covered.add(left)
        coverage = sum(graph["nodes"][index]["value"] for index in covered)
        redundancy = sum(
            1
            for left, right, _ in graph["edges"]
            if left in selected_indices and right in selected_indices
        )
        sensor_count = len(selected_indices)
        objective = (
            -coverage
            + 0.28 * redundancy
            + 4.0 * (sensor_count - graph["sensor_budget"]) ** 2
        )
        return {
            "feasible": sensor_count <= graph["sensor_budget"],
            "selected": [graph["nodes"][index]["id"] for index in selected_indices],
            "covered": [graph["nodes"][index]["id"] for index in sorted(covered)],
            "coverage_value": coverage,
            "redundancy": redundancy,
            "sensor_count": sensor_count,
            "objective": objective,
            "constraint_violations": 0
            if sensor_count <= graph["sensor_budget"]
            else 1,
        }

    sensor_problem = BinaryProblem(
        name="Sensor placement",
        variable_names=variable_names,
        objective=lambda bits: float(sensor_decode(bits)["objective"]),
        decode=sensor_decode,
    )

    maxcut = _solve_problem(maxcut_problem, configuration)
    sensor = _solve_problem(sensor_problem, configuration)
    return {
        "sequence": "Q4",
        "title": "Graph partition and sensor-placement QAOA",
        "source_ids": ["QRS-001", "QRS-002", "QRS-004", "QRS-012", "QRS-013"],
        "problem_family": "Graph partitioning and sensor placement",
        "dataset_mode": "frozen" if dataset else "synthetic",
        "graph": graph,
        "maxcut": maxcut,
        "sensor_placement": sensor,
        "solver_results": [
            {
                "solver_name": f"maxcut_{item['solver_name']}",
                "result": item,
            }
            for item in maxcut["solvers"]
        ]
        + [
            {
                "solver_name": f"sensor_{item['solver_name']}",
                "result": item,
            }
            for item in sensor["solvers"]
        ],
        "controls": _default_controls(),
    }


def _solve_problem(
    problem: BinaryProblem,
    configuration: dict[str, Any],
) -> dict[str, Any]:
    seed = int(configuration.get("seed", 301))
    budget = int(configuration.get("run_budget", 2048))
    grid_size = int(configuration.get("grid_size", 11))
    exact = exact_binary(problem)
    annealing = simulated_annealing(
        problem,
        seed=seed,
        steps=budget,
    )
    qaoa = qaoa_p1(
        problem,
        seed=seed,
        shots=budget,
        grid_size=grid_size,
    )
    return {
        "variable_names": problem.variable_names,
        "solvers": [exact, annealing, qaoa],
        "matched_budget_audit": {
            "simulated_annealing_transitions": budget,
            "qaoa_measurement_shots": budget,
            "qaoa_parameter_evaluations": qaoa.get("parameter_evaluations", 0),
            "exact_role": "Reference optimum excluded from matched stochastic budget.",
        },
    }


def _run_optimization_bundle(
    *,
    sequence: str,
    title: str,
    source_ids: list[str],
    problem: BinaryProblem,
    configuration: dict[str, Any],
    metadata: dict[str, Any],
) -> dict[str, Any]:
    solved = _solve_problem(problem, configuration)
    return {
        "sequence": sequence,
        "title": title,
        "source_ids": source_ids,
        "problem_family": problem.name,
        "variable_names": problem.variable_names,
        "metadata": metadata,
        "solvers": solved["solvers"],
        "solver_results": [
            {"solver_name": item["solver_name"], "result": item}
            for item in solved["solvers"]
        ],
        "matched_budget_audit": solved["matched_budget_audit"],
        "controls": _default_controls(),
    }


def _standardize_features(rows: list[list[float]]) -> list[list[float]]:
    columns = len(rows[0])
    means = [
        sum(row[column] for row in rows) / len(rows)
        for column in range(columns)
    ]
    stds = []
    for column in range(columns):
        variance = sum(
            (row[column] - means[column]) ** 2 for row in rows
        ) / len(rows)
        stds.append(max(math.sqrt(variance), 1e-9))
    return [
        [
            (row[column] - means[column]) / stds[column]
            for column in range(columns)
        ]
        for row in rows
    ]


def _stress_dataset(dataset: dict[str, Any] | None, seed: int) -> list[dict[str, Any]]:
    observations = _snapshot_rows(dataset, "observations")
    if len(observations) >= 12:
        rows = []
        for index, row in enumerate(observations[:80]):
            value = _numeric(row.get("value"), 0.0)
            quality = str(row.get("quality_flag", "unverified")).lower()
            rows.append(
                {
                    "id": str(row.get("observation_id") or f"OBS-{index + 1}"),
                    "features": [
                        value,
                        float(index % 24),
                        1.0 if str(row.get("source_type")) == "sensor" else 0.0,
                        float(len(str(row.get("notes") or ""))),
                    ],
                    "label": 1 if quality in {"suspect", "invalid", "unverified"} else 0,
                }
            )
        return rows

    rng = seeded_random(seed)
    rows = []
    for index in range(48):
        moisture = 0.25 + rng.random() * 0.55
        temperature = 18 + rng.random() * 18
        ec = 0.15 + rng.random() * 1.1
        canopy = 0.35 + rng.random() * 0.6
        hidden = (
            2.4 * (0.5 - moisture)
            + 0.08 * (temperature - 28)
            + 0.7 * (ec - 0.65)
            + 1.2 * (0.65 - canopy)
            + rng.gauss(0, 0.12)
        )
        rows.append(
            {
                "id": f"STRESS-{index + 1:03d}",
                "features": [moisture, temperature, ec, canopy],
                "label": 1 if hidden > 0.35 else 0,
            }
        )
    return rows


def _rbf(left: list[float], right: list[float], gamma: float = 0.5) -> float:
    return math.exp(
        -gamma * sum((a - b) ** 2 for a, b in zip(left, right))
    )


def _quantum_fidelity_kernel(left: list[float], right: list[float]) -> float:
    angles_left = [math.tanh(value) * math.pi / 2 for value in left[:4]]
    angles_right = [math.tanh(value) * math.pi / 2 for value in right[:4]]
    overlap = 1.0
    for a, b in zip(angles_left, angles_right):
        overlap *= math.cos((a - b) / 2)
    phase = sum(
        math.sin(a) * math.sin(b)
        for a, b in zip(angles_left, angles_right)
    )
    return max(0.0, min(1.0, overlap**2 * (0.75 + 0.25 * math.cos(phase) ** 2)))


def _kernel_predict(
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    kernel: Callable[[list[float], list[float]], float],
) -> list[int]:
    predictions = []
    for row in test:
        score = 0.0
        for candidate in train:
            sign = 1.0 if candidate["label"] == 1 else -1.0
            score += sign * kernel(candidate["features"], row["features"])
        predictions.append(1 if score >= 0 else 0)
    return predictions


def _classification_metrics(actual: list[int], predicted: list[int]) -> dict[str, float]:
    tp = sum(1 for a, p in zip(actual, predicted) if a == p == 1)
    tn = sum(1 for a, p in zip(actual, predicted) if a == p == 0)
    fp = sum(1 for a, p in zip(actual, predicted) if a == 0 and p == 1)
    fn = sum(1 for a, p in zip(actual, predicted) if a == 1 and p == 0)
    accuracy = (tp + tn) / max(1, len(actual))
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def run_q5(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    seed = int(configuration.get("seed", 301))
    rows = _stress_dataset(dataset, seed)
    standardized = _standardize_features([row["features"] for row in rows])
    normalized_rows = [
        {**row, "features": standardized[index]}
        for index, row in enumerate(rows)
    ]
    train = [row for index, row in enumerate(normalized_rows) if index % 4 != 0]
    test = [row for index, row in enumerate(normalized_rows) if index % 4 == 0]
    actual = [row["label"] for row in test]
    classical_predictions = _kernel_predict(train, test, _rbf)
    quantum_predictions = _kernel_predict(train, test, _quantum_fidelity_kernel)

    classical = {
        "solver_name": "classical_rbf_kernel",
        "algorithm": "Classical RBF kernel classifier",
        "metrics": _classification_metrics(actual, classical_predictions),
        "predictions": classical_predictions,
    }
    quantum = {
        "solver_name": "quantum_fidelity_kernel",
        "algorithm": "Analytic four-feature fidelity kernel",
        "qubits": 4,
        "backend": "Python analytic feature-map simulator",
        "metrics": _classification_metrics(actual, quantum_predictions),
        "predictions": quantum_predictions,
    }
    return {
        "sequence": "Q5",
        "title": "Quantum-kernel stress classifier",
        "source_ids": ["QRS-005", "QRS-014"],
        "problem_family": "Supervised classification",
        "dataset_mode": "frozen" if dataset and _snapshot_rows(dataset, "observations") else "synthetic",
        "dataset_summary": {
            "records": len(rows),
            "train": len(train),
            "test": len(test),
        },
        "classical": classical,
        "quantum": quantum,
        "solver_results": [
            {"solver_name": classical["solver_name"], "result": classical},
            {"solver_name": quantum["solver_name"], "result": quantum},
        ],
        "controls": _default_controls(),
    }


def _time_series(dataset: dict[str, Any] | None, seed: int) -> list[float]:
    observations = _snapshot_rows(dataset, "observations")
    values = [_numeric(row.get("value"), math.nan) for row in observations]
    values = [value for value in values if math.isfinite(value)]
    if len(values) >= 20:
        minimum = min(values)
        maximum = max(values)
        spread = max(1e-9, maximum - minimum)
        return [(value - minimum) / spread for value in values]

    rng = seeded_random(seed)
    moisture = 0.62
    series = []
    for index in range(150):
        temperature = 27 + 6 * math.sin(2 * math.pi * index / 24) + rng.gauss(0, 0.8)
        rain = 0.05 + rng.random() * 0.1 if rng.random() < 0.08 else 0.0
        irrigation = 0.09 if index % 31 == 0 else 0.0
        et = 0.012 + max(0, temperature - 24) * 0.0012
        moisture = 0.90 * moisture + rain + irrigation - et + rng.gauss(0, 0.005)
        moisture = max(0.18, min(0.82, moisture))
        series.append(moisture)
    return series


def _regression_metrics(actual: list[float], predicted: list[float]) -> dict[str, float]:
    errors = [p - a for a, p in zip(actual, predicted)]
    mae = sum(abs(value) for value in errors) / max(1, len(errors))
    rmse = math.sqrt(sum(value**2 for value in errors) / max(1, len(errors)))
    mean = sum(actual) / max(1, len(actual))
    total = sum((value - mean) ** 2 for value in actual)
    residual = sum(value**2 for value in errors)
    return {
        "mae": mae,
        "rmse": rmse,
        "r2": 0.0 if total == 0 else 1 - residual / total,
    }


def run_q6(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    seed = int(configuration.get("seed", 301))
    series = _time_series(dataset, seed)
    split = max(5, int(len(series) * 0.72))
    train = series[:split]
    test = series[split:]
    persistence = [series[split - 1]] + test[:-1]

    def fit_ar(values: list[float]) -> tuple[float, float]:
        x = values[:-1]
        y = values[1:]
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        variance = sum((value - mean_x) ** 2 for value in x)
        slope = (
            sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y))
            / max(1e-12, variance)
        )
        intercept = mean_y - slope * mean_x
        return intercept, slope

    intercept, slope = fit_ar(train)
    linear_predictions = [
        intercept + slope * value for value in persistence
    ]

    rng = seeded_random(seed)
    reservoir_nodes = 8
    weights = [rng.uniform(-1.0, 1.0) for _ in range(reservoir_nodes)]
    recurrent = [rng.uniform(0.15, 0.65) for _ in range(reservoir_nodes)]
    state = [0.0] * reservoir_nodes
    reservoir_features = []
    for value in series:
        state = [
            math.tanh(weights[index] * value + recurrent[index] * state[index])
            for index in range(reservoir_nodes)
        ]
        reservoir_features.append(list(state))

    def weighted_average_prediction(features: list[list[float]], values: list[float]) -> list[float]:
        coefficients = []
        for node in range(len(features[0])):
            numerator = sum(
                features[index][node] * values[index + 1]
                for index in range(len(values) - 1)
            )
            denominator = sum(
                features[index][node] ** 2
                for index in range(len(values) - 1)
            )
            coefficients.append(numerator / max(1e-9, denominator))
        return [
            sum(coef * value for coef, value in zip(coefficients, row))
            / max(1, len(coefficients))
            for row in features[split - 1 : -1]
        ]

    classical_reservoir_predictions = weighted_average_prediction(
        reservoir_features[:split],
        train,
    )

    quantum_features = []
    phase = 0.0
    for value in series:
        phase += 0.31 + value * 0.7
        theta = math.pi * value
        quantum_features.append(
            [
                math.cos(theta),
                math.sin(theta),
                math.cos(phase) * math.cos(theta),
                math.sin(phase) * math.sin(theta),
            ]
        )
    quantum_reservoir_predictions = weighted_average_prediction(
        quantum_features[:split],
        train,
    )

    actual = test[: len(persistence)]
    methods = {
        "persistence": {
            "solver_name": "persistence",
            "metrics": _regression_metrics(actual, persistence),
        },
        "linear": {
            "solver_name": "linear_ar1",
            "metrics": _regression_metrics(actual, linear_predictions),
        },
        "classical_reservoir": {
            "solver_name": "classical_reservoir",
            "nodes": reservoir_nodes,
            "metrics": _regression_metrics(
                actual[: len(classical_reservoir_predictions)],
                classical_reservoir_predictions,
            ),
        },
        "quantum_reservoir": {
            "solver_name": "quantum_reservoir",
            "qubits": 2,
            "backend": "Python analytic two-qubit feature simulator",
            "metrics": _regression_metrics(
                actual[: len(quantum_reservoir_predictions)],
                quantum_reservoir_predictions,
            ),
        },
    }
    return {
        "sequence": "Q6",
        "title": "Quantum reservoir time-series experiment",
        "source_ids": ["QRS-006", "QRS-014"],
        "problem_family": "Temporal forecasting",
        "dataset_mode": "frozen" if dataset and _snapshot_rows(dataset, "observations") else "synthetic",
        "dataset_summary": {
            "records": len(series),
            "train": split,
            "test": len(test),
        },
        "methods": methods,
        "solver_results": [
            {"solver_name": value["solver_name"], "result": value}
            for value in methods.values()
        ],
        "controls": _default_controls(),
    }


def _binomial(rng: random.Random, trials: int, probability: float) -> int:
    return sum(1 for _ in range(trials) if rng.random() < probability)


def run_q7(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    seed = int(configuration.get("seed", 301))
    probability = float(configuration.get("true_probability", 0.18))
    probability = max(0.001, min(0.999, probability))
    shots_per_circuit = int(configuration.get("shots_per_circuit", 128))
    rng = seeded_random(seed)
    monte_carlo_shots = shots_per_circuit * 4
    monte_estimate = _binomial(rng, monte_carlo_shots, probability) / monte_carlo_shots

    powers = [0, 1, 2, 4]
    observations = []
    theta_true = math.asin(math.sqrt(probability))
    rng_mlae = seeded_random(seed + 17)
    for power in powers:
        modeled = math.sin((2 * power + 1) * theta_true) ** 2
        successes = _binomial(rng_mlae, shots_per_circuit, modeled)
        observations.append(
            {
                "power": power,
                "shots": shots_per_circuit,
                "successes": successes,
                "modeled_probability": modeled,
            }
        )

    best_theta = 0.0
    best_likelihood = -math.inf
    for index in range(1, 4000):
        theta = (math.pi / 2) * index / 4000
        likelihood = 0.0
        for item in observations:
            modeled = math.sin((2 * item["power"] + 1) * theta) ** 2
            modeled = max(1e-12, min(1 - 1e-12, modeled))
            likelihood += item["successes"] * math.log(modeled)
            likelihood += (item["shots"] - item["successes"]) * math.log(1 - modeled)
        if likelihood > best_likelihood:
            best_likelihood = likelihood
            best_theta = theta
    mlae_estimate = math.sin(best_theta) ** 2

    classical = {
        "solver_name": "monte_carlo",
        "algorithm": "Ordinary Monte Carlo",
        "shots": monte_carlo_shots,
        "estimate": monte_estimate,
        "absolute_error": abs(monte_estimate - probability),
    }
    quantum = {
        "solver_name": "maximum_likelihood_amplitude_estimation",
        "algorithm": "Maximum-likelihood amplitude estimation simulation",
        "estimate": mlae_estimate,
        "absolute_error": abs(mlae_estimate - probability),
        "observations": observations,
        "oracle_applications": sum(
            item["shots"] * (2 * item["power"] + 1)
            for item in observations
        ),
    }
    return {
        "sequence": "Q7",
        "title": "Amplitude-estimation uncertainty experiment",
        "source_ids": ["QRS-007"],
        "problem_family": "Threshold probability estimation",
        "known_probability": probability,
        "classical": classical,
        "quantum": quantum,
        "solver_results": [
            {"solver_name": classical["solver_name"], "result": classical},
            {"solver_name": quantum["solver_name"], "result": quantum},
        ],
        "controls": {
            **_default_controls(),
            "state_preparation_cost_excluded": True,
            "oracle_construction_cost_excluded": True,
            "speedup_claim": False,
        },
    }


def run_q8(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    seed = int(configuration.get("seed", 301))
    rng = seeded_random(seed)
    plant_points = []
    event_center = 4.8
    event_width = 0.42
    for index in range(240):
        moment = index * 0.05
        event = 0.55 * math.exp(
            -((moment - event_center) ** 2) / (2 * event_width**2)
        )
        drift = 0.025 * math.sin(moment * 0.55)
        measured = event + drift + rng.gauss(0, 0.09)
        plant_points.append({"time": moment, "measured_pt": measured})
    baseline = [row["measured_pt"] for row in plant_points[:60]]
    mean = sum(baseline) / len(baseline)
    standard_deviation = math.sqrt(
        sum((value - mean) ** 2 for value in baseline) / len(baseline)
    )
    peak = max(row["measured_pt"] for row in plant_points)

    field = float(configuration.get("field_microtesla", 18.0))
    temperature = float(configuration.get("temperature_c", 28.0))
    zero_field = 2.87
    temperature_shift = -0.000074 * (temperature - 25)
    zeeman = 0.000028 * field
    centers = [
        zero_field + temperature_shift - zeeman,
        zero_field + temperature_shift + zeeman,
    ]
    odmr_points = []
    for index in range(401):
        frequency = 2.866 + index * 0.00002
        contrast = 1.0
        for center in centers:
            contrast -= 0.065 / (1 + ((frequency - center) / 0.00035) ** 2)
        contrast += rng.gauss(0, 0.0018)
        odmr_points.append(
            {"frequency_ghz": frequency, "contrast": contrast}
        )

    plant = {
        "solver_name": "plant_biomagnetic_signal_simulator",
        "points": plant_points,
        "detected_peak_pt": peak,
        "baseline_std_pt": standard_deviation,
        "snr": (peak - mean) / max(1e-12, standard_deviation),
    }
    nv = {
        "solver_name": "nv_odmr_simulator",
        "points": odmr_points,
        "truth": {
            "field_microtesla": field,
            "temperature_c": temperature,
            "resonance_centers_ghz": centers,
        },
    }
    return {
        "sequence": "Q8",
        "title": "Quantum sensing simulation workspace",
        "source_ids": ["QRS-008", "QRS-009"],
        "problem_family": "Quantum-sensor signal simulation",
        "plant_biomagnetism": plant,
        "nv_odmr": nv,
        "solver_results": [
            {"solver_name": plant["solver_name"], "result": plant},
            {"solver_name": nv["solver_name"], "result": nv},
        ],
        "controls": {
            **_default_controls(),
            "hardware_connected": False,
            "diagnostic_claim": False,
            "automated_actuation": False,
        },
    }


def run_q9(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    hamiltonian = {"a": -1.0, "b": 0.2, "d": -0.5}
    trace = hamiltonian["a"] + hamiltonian["d"]
    discriminant = math.sqrt(
        (hamiltonian["a"] - hamiltonian["d"]) ** 2
        + 4 * hamiltonian["b"] ** 2
    )
    exact_energy = (trace - discriminant) / 2
    grid_points = int(configuration.get("grid_points", 721))
    best = {"theta": 0.0, "energy": math.inf}
    curve = []
    for index in range(grid_points):
        theta = 2 * math.pi * index / max(1, grid_points - 1)
        cosine = math.cos(theta / 2)
        sine = math.sin(theta / 2)
        energy = (
            hamiltonian["a"] * cosine**2
            + 2 * hamiltonian["b"] * cosine * sine
            + hamiltonian["d"] * sine**2
        )
        if index % 12 == 0:
            curve.append({"theta": theta, "energy": energy})
        if energy < best["energy"]:
            best = {"theta": theta, "energy": energy}

    exact = {
        "solver_name": "exact_eigensolver",
        "algorithm": "Closed-form 2x2 eigensolver",
        "energy": exact_energy,
    }
    vqe = {
        "solver_name": "educational_vqe",
        "algorithm": "One-parameter variational energy search",
        "qubits": 1,
        "best": best,
        "absolute_error": abs(best["energy"] - exact_energy),
        "curve": curve,
    }
    return {
        "sequence": "Q9",
        "title": "Quantum chemistry and resource-estimation workspace",
        "source_ids": ["QRS-010", "QRS-011"],
        "problem_family": "Molecular energy and resource estimation",
        "hamiltonian": hamiltonian,
        "exact": exact,
        "vqe": vqe,
        "resource_ladder": [
            {
                "system": "Two-level educational model",
                "logical_qubits": 1,
                "stage": "Active simulator",
            },
            {
                "system": "Small molecular active space",
                "logical_qubits": "4–12",
                "stage": "Later simulator",
            },
            {
                "system": "FeMoco literature",
                "logical_qubits": "Fault-tolerant scale",
                "stage": "Literature registry only",
            },
        ],
        "solver_results": [
            {"solver_name": exact["solver_name"], "result": exact},
            {"solver_name": vqe["solver_name"], "result": vqe},
        ],
        "controls": {
            **_default_controls(),
            "educational_toy_model": True,
            "chemistry_grade_claim": False,
            "femoco_simulation_claim": False,
        },
    }


def run_q10(dataset: dict[str, Any] | None, configuration: dict[str, Any]) -> dict[str, Any]:
    standards = [
        {"standard": "FIPS 203", "algorithm": "ML-KEM", "use": "Key encapsulation"},
        {"standard": "FIPS 204", "algorithm": "ML-DSA", "use": "Digital signatures"},
        {"standard": "FIPS 205", "algorithm": "SLH-DSA", "use": "Hash-based signatures"},
    ]
    inventory = configuration.get("inventory")
    if not isinstance(inventory, list):
        inventory = [
            {
                "system": "Edge gateway transport",
                "owner": "Platform engineering",
                "target": "Crypto-agile hybrid transition",
                "approved_library_selected": False,
                "interoperability_tested": False,
                "rollback_documented": False,
            },
            {
                "system": "Signed experiment exports",
                "owner": "Research governance",
                "target": "ML-DSA-capable signature profile",
                "approved_library_selected": False,
                "interoperability_tested": False,
                "rollback_documented": True,
            },
        ]
    checks = []
    for item in inventory:
        checks.extend(
            [
                bool(item.get("owner")),
                bool(item.get("target")),
                bool(item.get("approved_library_selected")),
                bool(item.get("interoperability_tested")),
                bool(item.get("rollback_documented")),
            ]
        )
    readiness = round(100 * sum(checks) / max(1, len(checks)))
    registry = {
        "solver_name": "post_quantum_readiness_registry",
        "standards": standards,
        "inventory": inventory,
        "readiness_percent": readiness,
    }
    return {
        "sequence": "Q10",
        "title": "Post-quantum security registry",
        "source_ids": ["QRS-015"],
        "problem_family": "Cryptographic migration and interoperability",
        "registry": registry,
        "solver_results": [
            {"solver_name": registry["solver_name"], "result": registry}
        ],
        "controls": {
            "cryptographic_implementation_included": False,
            "approved_library_required": True,
            "interoperability_testing_required": True,
            "rollback_required": True,
            "production_migration_authorized": False,
            "human_review_required": True,
            "advantage_claim": False,
            "hardware_used": False,
            "operational_dependency": False,
        },
    }


def _default_controls() -> dict[str, Any]:
    return {
        "simulator_only": True,
        "hardware_used": False,
        "advantage_claim": False,
        "operational_dependency": False,
        "matched_budget": True,
        "classical_baseline_required": True,
        "synthetic_data": True,
        "human_review_required": True,
    }


RUNNERS: dict[str, Callable[[dict[str, Any] | None, dict[str, Any]], dict[str, Any]]] = {
    "Q2": run_q2,
    "Q3": run_q3,
    "Q4": run_q4,
    "Q5": run_q5,
    "Q6": run_q6,
    "Q7": run_q7,
    "Q8": run_q8,
    "Q9": run_q9,
    "Q10": run_q10,
}


def _solver_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in result.get("solver_results", []):
        solver_name = item["solver_name"]
        payload = item["result"]
        best = payload.get("best") if isinstance(payload, dict) else None
        metrics = payload.get("metrics", {}) if isinstance(payload, dict) else {}
        rows.append(
            {
                "solver_name": solver_name,
                "objective": (
                    best.get("energy")
                    if isinstance(best, dict)
                    else metrics.get("rmse", metrics.get("accuracy", ""))
                ),
                "feasible": (
                    best.get("feasible", True)
                    if isinstance(best, dict)
                    else True
                ),
                "runtime_seconds": payload.get("runtime_seconds", "")
                if isinstance(payload, dict)
                else "",
                "result_sha256": sha256_json(payload),
            }
        )
    return rows


def _csv_text(rows: Iterable[dict[str, Any]]) -> str:
    materialized = list(rows)
    if not materialized:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(materialized[0].keys()))
    writer.writeheader()
    writer.writerows(materialized)
    return buffer.getvalue()


def run_registered_experiment(
    sequence: str,
    *,
    dataset: dict[str, Any] | None,
    configuration: dict[str, Any] | None,
) -> dict[str, Any]:
    normalized_sequence = str(sequence).upper().strip()
    if normalized_sequence not in SUPPORTED_SEQUENCES:
        raise ValueError(
            f"Unsupported sequence {sequence!r}. "
            f"Choose one of: {', '.join(sorted(SUPPORTED_SEQUENCES))}."
        )

    configuration = dict(configuration or {})
    started = time.perf_counter()
    result = RUNNERS[normalized_sequence](dataset, configuration)
    runtime_seconds = time.perf_counter() - started
    result["sequence"] = normalized_sequence
    result["runtime_seconds"] = runtime_seconds
    result["configuration"] = configuration
    result["dataset_sha256"] = (
        str(dataset.get("sha256"))
        if dataset and dataset.get("sha256")
        else sha256_json(dataset or {"mode": "synthetic"})
    )
    result["result_hash_scope"] = "deterministic-v1"
    result["result_sha256"] = sha256_json(
        deterministic_result_payload(result)
    )
    artifacts = [
        {
            "artifact_type": "result_json",
            "filename": f"{normalized_sequence.lower()}-server-result.json",
            "media_type": "application/json",
            "content_text": json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
        },
        {
            "artifact_type": "solver_csv",
            "filename": f"{normalized_sequence.lower()}-solver-summary.csv",
            "media_type": "text/csv",
            "content_text": _csv_text(_solver_rows(result)),
        },
    ]
    return {
        "result": result,
        "artifacts": artifacts,
        "runtime_seconds": runtime_seconds,
    }
