from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "publication_tables"

EXACT_RESULTS_TABLE = TABLE_DIR / "exact_validation_results.csv"
ENERGY_AUDIT_SUMMARY_TABLE = TABLE_DIR / "qubo_energy_audit_summary.csv"
ISING_COEFFICIENTS_TABLE = TABLE_DIR / "qubo_to_ising_coefficients.csv"
FINAL_EXACT_BENCHMARK_TABLE = TABLE_DIR / "final_publication_benchmark_with_exact_validation.csv"
INTEGRATED_SUMMARY_TABLE = TABLE_DIR / "exact_validation_integrated_summary.csv"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def safe_float(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def safe_int(value: Any) -> int | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except ValueError:
        return None


def first_rows(rows: List[Dict[str, str]], limit: int = 8) -> List[Dict[str, str]]:
    return rows[:limit]


def exact_validation_summary(exact_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    if not exact_rows:
        return {
            "sequence_count": 0,
            "enumerated_count": 0,
            "feasible_count": 0,
            "total_assignments": 0,
            "minimum_energy_best": None,
            "minimum_energy_worst": None,
            "average_variable_count": None,
        }

    enumerated_count = 0
    feasible_count = 0
    total_assignments = 0
    energies: List[float] = []
    variables: List[int] = []

    for row in exact_rows:
        if str(row.get("enumerated", "")).lower() == "true":
            enumerated_count += 1

        if str(row.get("feasible", "")).lower() == "true":
            feasible_count += 1

        assignments = safe_int(row.get("assignment_count"))
        if assignments is not None:
            total_assignments += assignments

        energy = safe_float(row.get("exact_minimum_energy"))
        if energy is not None:
            energies.append(energy)

        variable_count = safe_int(row.get("variable_count"))
        if variable_count is not None:
            variables.append(variable_count)

    return {
        "sequence_count": len(exact_rows),
        "enumerated_count": enumerated_count,
        "feasible_count": feasible_count,
        "total_assignments": total_assignments,
        "minimum_energy_best": min(energies) if energies else None,
        "minimum_energy_worst": max(energies) if energies else None,
        "average_variable_count": round(sum(variables) / len(variables), 3) if variables else None,
    }


def energy_summary(energy_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    totals: List[float] = []
    linear_values: List[float] = []
    overlap_values: List[float] = []
    crossing_values: List[float] = []

    for row in energy_rows:
        total = safe_float(row.get("total_energy"))
        linear = safe_float(row.get("linear_energy"))
        overlap = safe_float(row.get("overlap_penalty_energy"))
        crossing = safe_float(row.get("crossing_penalty_energy"))

        if total is not None:
            totals.append(total)
        if linear is not None:
            linear_values.append(linear)
        if overlap is not None:
            overlap_values.append(overlap)
        if crossing is not None:
            crossing_values.append(crossing)

    return {
        "audited_sequence_count": len(energy_rows),
        "best_total_energy": min(totals) if totals else None,
        "worst_total_energy": max(totals) if totals else None,
        "total_linear_energy": round(sum(linear_values), 6) if linear_values else 0,
        "total_overlap_penalty": round(sum(overlap_values), 6) if overlap_values else 0,
        "total_crossing_penalty": round(sum(crossing_values), 6) if crossing_values else 0,
    }


def ising_summary(ising_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    sequence_ids = set()
    constant_count = 0
    h_count = 0
    j_count = 0
    values: List[float] = []

    for row in ising_rows:
        sequence_id = row.get("sequence_id", "")
        if sequence_id:
            sequence_ids.add(sequence_id)

        coefficient_type = row.get("coefficient_type", "")

        if coefficient_type == "constant_offset":
            constant_count += 1
        elif coefficient_type == "linear_field":
            h_count += 1
        elif coefficient_type == "coupling":
            j_count += 1

        value = safe_float(row.get("value"))
        if value is not None:
            values.append(value)

    return {
        "sequence_count": len(sequence_ids),
        "constant_offset_count": constant_count,
        "linear_field_count": h_count,
        "coupling_count": j_count,
        "min_coefficient_value": min(values) if values else None,
        "max_coefficient_value": max(values) if values else None,
    }


def benchmark_summary(benchmark_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    exact_available = 0
    exact_control = 0

    for row in benchmark_rows:
        if str(row.get("phase41_exact_ground_truth_available", "")).lower() == "true":
            exact_available += 1

        if row.get("phase41_row_type") == "exact_validation_control_row":
            exact_control += 1

    return {
        "integrated_benchmark_rows": len(benchmark_rows),
        "rows_with_exact_ground_truth": exact_available,
        "exact_validation_control_rows": exact_control,
    }


def file_status() -> Dict[str, Any]:
    files = {
        "exact_validation_results": EXACT_RESULTS_TABLE,
        "qubo_energy_audit_summary": ENERGY_AUDIT_SUMMARY_TABLE,
        "qubo_to_ising_coefficients": ISING_COEFFICIENTS_TABLE,
        "final_benchmark_with_exact_validation": FINAL_EXACT_BENCHMARK_TABLE,
        "exact_validation_integrated_summary": INTEGRATED_SUMMARY_TABLE,
    }

    return {
        name: {
            "exists": path.exists(),
            "path": str(path),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }
        for name, path in files.items()
    }


def run_exact_validation_dashboard() -> Dict[str, Any]:
    exact_rows = read_csv(EXACT_RESULTS_TABLE)
    energy_rows = read_csv(ENERGY_AUDIT_SUMMARY_TABLE)
    ising_rows = read_csv(ISING_COEFFICIENTS_TABLE)
    benchmark_rows = read_csv(FINAL_EXACT_BENCHMARK_TABLE)
    integrated_summary_rows = read_csv(INTEGRATED_SUMMARY_TABLE)

    return {
        "success": True,
        "title": "Phase 42 Exact Validation Dashboard",
        "summary": {
            "exact_validation": exact_validation_summary(exact_rows),
            "energy_audit": energy_summary(energy_rows),
            "ising_mapping": ising_summary(ising_rows),
            "integrated_benchmark": benchmark_summary(benchmark_rows),
        },
        "tables": {
            "exact_validation_results": first_rows(exact_rows),
            "energy_audit_summary": first_rows(energy_rows),
            "ising_coefficients": first_rows(ising_rows),
            "final_benchmark_with_exact_validation": first_rows(benchmark_rows),
            "exact_validation_integrated_summary": first_rows(integrated_summary_rows),
        },
        "file_status": file_status(),
        "interpretation": [
            "Exact validation gives small-instance ground truth for the RNA Stem-QUBO model.",
            "Energy audit separates linear reward, overlap penalty, crossing penalty, and total QUBO energy.",
            "QUBO-to-Ising coefficients support QAOA/VQE cost-Hamiltonian interpretation.",
            "This supports auditability, but it does not claim quantum advantage or final biological validation.",
        ],
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_exact_validation_dashboard(), indent=2))
