from __future__ import annotations

import csv
import math
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence, Set, Tuple

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False
    plt = None


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "publication_tables"
FIGURE_DIR = ROOT / "results" / "publication_figures"
DOCS_DIR = ROOT / "docs"

TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

MIN_LOOP = 3
MAX_QUBO_VARIABLES = 30
RANDOM_SEED = 37

RNA_DATASET = [
    {
        "sequence_id": "RNA_01_demo",
        "sequence": "GGCGCAAAACUUGUCGAAUGAGAACAAAUAACAGAAUUUGCUUG",
        "source": "project_demo_sequence",
        "notes": "Primary dashboard demonstration sequence",
    },
    {
        "sequence_id": "RNA_02_short_hairpin",
        "sequence": "GGGAAAUCC",
        "source": "synthetic_control",
        "notes": "Small hairpin-like control for exact-size testing",
    },
    {
        "sequence_id": "RNA_03_medium_control",
        "sequence": "AUGGCUACGUAGCUA",
        "source": "synthetic_control",
        "notes": "Medium control sequence for QUBO and solver comparison",
    },
    {
        "sequence_id": "RNA_04_gc_rich",
        "sequence": "GCGCGAUUCGCGC",
        "source": "synthetic_control",
        "notes": "GC-rich sequence for candidate-pair growth testing",
    },
    {
        "sequence_id": "RNA_05_balanced",
        "sequence": "AUGCUUCGGAUACGCUAGCUA",
        "source": "synthetic_control",
        "notes": "Balanced sequence for benchmark comparison",
    },
    {
        "sequence_id": "RNA_06_longer_control",
        "sequence": "GGAUACGUAGCUAGGCUAACGCUUAGC",
        "source": "synthetic_control",
        "notes": "Longer controlled sequence for scaling and compression estimates",
    },
]

PAIR_RULES = {
    ("A", "U"),
    ("U", "A"),
    ("G", "C"),
    ("C", "G"),
    ("G", "U"),
    ("U", "G"),
}


def clean_sequence(sequence: str) -> str:
    cleaned = sequence.upper().replace("T", "U")
    return "".join(base for base in cleaned if base in {"A", "U", "G", "C"})


def gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0

    gc_count = sum(1 for base in sequence if base in {"G", "C"})
    return round(100.0 * gc_count / len(sequence), 3)


def can_pair(left: str, right: str) -> bool:
    return (left, right) in PAIR_RULES


def all_pair_universe(length: int, min_loop: int = MIN_LOOP) -> Set[Tuple[int, int]]:
    return {
        (i, j)
        for i in range(length)
        for j in range(i + min_loop + 1, length)
    }


def candidate_pairs(sequence: str, min_loop: int = MIN_LOOP) -> List[Tuple[int, int]]:
    pairs: List[Tuple[int, int]] = []

    for i in range(len(sequence)):
        for j in range(i + min_loop + 1, len(sequence)):
            if can_pair(sequence[i], sequence[j]):
                pairs.append((i, j))

    return pairs


def nussinov_reference_pairs(sequence: str, min_loop: int = MIN_LOOP) -> Set[Tuple[int, int]]:
    n = len(sequence)

    if n == 0:
        return set()

    dp = [[0 for _ in range(n)] for _ in range(n)]

    for span in range(1, n):
        for i in range(0, n - span):
            j = i + span

            best = dp[i + 1][j] if i + 1 <= j else 0
            best = max(best, dp[i][j - 1] if i <= j - 1 else 0)

            if j - i > min_loop and can_pair(sequence[i], sequence[j]):
                diagonal = dp[i + 1][j - 1] if i + 1 <= j - 1 else 0
                best = max(best, diagonal + 1)

            for k in range(i + 1, j):
                best = max(best, dp[i][k] + dp[k + 1][j])

            dp[i][j] = best

    pairs: Set[Tuple[int, int]] = set()

    def traceback(i: int, j: int) -> None:
        if i >= j:
            return

        current = dp[i][j]

        if i + 1 <= j and current == dp[i + 1][j]:
            traceback(i + 1, j)
            return

        if i <= j - 1 and current == dp[i][j - 1]:
            traceback(i, j - 1)
            return

        if j - i > min_loop and can_pair(sequence[i], sequence[j]):
            diagonal = dp[i + 1][j - 1] if i + 1 <= j - 1 else 0

            if current == diagonal + 1:
                pairs.add((i, j))
                traceback(i + 1, j - 1)
                return

        for k in range(i + 1, j):
            if current == dp[i][k] + dp[k + 1][j]:
                traceback(i, k)
                traceback(k + 1, j)
                return

    traceback(0, n - 1)
    return pairs


def make_dot_bracket(length: int, pairs: Set[Tuple[int, int]]) -> str:
    chars = ["." for _ in range(length)]

    for i, j in pairs:
        if 0 <= i < length and 0 <= j < length:
            chars[i] = "("
            chars[j] = ")"

    return "".join(chars)


def stem_score(sequence: str, pairs: Sequence[Tuple[int, int]]) -> float:
    score = 0.0

    for i, j in pairs:
        pair = (sequence[i], sequence[j])

        if pair in {("G", "C"), ("C", "G")}:
            score += 3.0
        elif pair in {("A", "U"), ("U", "A")}:
            score += 2.0
        else:
            score += 1.0

    return score


def candidate_stems(
    sequence: str,
    min_stem_length: int = 2,
    max_stem_length: int = 4,
) -> List[Tuple[Tuple[int, int], ...]]:
    stems: Set[Tuple[Tuple[int, int], ...]] = set()
    pairs = set(candidate_pairs(sequence))

    for i, j in sorted(pairs):
        current: List[Tuple[int, int]] = []

        for offset in range(max_stem_length):
            left = i + offset
            right = j - offset

            if left >= right:
                break

            if (left, right) not in pairs:
                break

            current.append((left, right))

        if len(current) >= min_stem_length:
            stems.add(tuple(current))

    if not stems:
        for pair in sorted(pairs):
            stems.add((pair,))

    sorted_stems = sorted(
        stems,
        key=lambda item: (stem_score(sequence, item), len(item)),
        reverse=True,
    )

    return sorted_stems[:MAX_QUBO_VARIABLES]


def stems_incompatible(
    stem_a: Sequence[Tuple[int, int]],
    stem_b: Sequence[Tuple[int, int]],
) -> bool:
    bases_a = {base for pair in stem_a for base in pair}
    bases_b = {base for pair in stem_b for base in pair}

    if bases_a.intersection(bases_b):
        return True

    for i, j in stem_a:
        for k, l in stem_b:
            if i < k < j < l:
                return True

            if k < i < l < j:
                return True

    return False


def build_qubo(sequence: str) -> Dict[str, Any]:
    stems = candidate_stems(sequence)
    variables = []

    for index, stem in enumerate(stems):
        variables.append(
            {
                "variable": f"s_{index}",
                "stem_pairs": list(stem),
                "stem_length": len(stem),
                "stem_score": round(stem_score(sequence, stem), 3),
                "linear_weight": round(-stem_score(sequence, stem), 3),
            }
        )

    quadratic_terms = []

    for i in range(len(stems)):
        for j in range(i + 1, len(stems)):
            if stems_incompatible(stems[i], stems[j]):
                quadratic_terms.append(
                    {
                        "var_i": f"s_{i}",
                        "var_j": f"s_{j}",
                        "penalty": 6.0,
                    }
                )

    possible_quadratic = max(1, len(stems) * (len(stems) - 1) / 2)
    qubo_density = round(len(quadratic_terms) / possible_quadratic, 4)

    return {
        "variables": variables,
        "quadratic_terms": quadratic_terms,
        "variable_count": len(variables),
        "linear_term_count": len(variables),
        "quadratic_term_count": len(quadratic_terms),
        "qubo_density": qubo_density,
    }


def qubo_energy(bits: List[int], qubo: Dict[str, Any]) -> float:
    variables = qubo["variables"]
    energy = 0.0

    for index, bit in enumerate(bits):
        if bit:
            energy += variables[index]["linear_weight"]

    for term in qubo["quadratic_terms"]:
        i = int(term["var_i"].split("_")[1])
        j = int(term["var_j"].split("_")[1])

        if bits[i] and bits[j]:
            energy += term["penalty"]

    return round(energy, 6)


def solution_pairs(bits: List[int], qubo: Dict[str, Any]) -> Set[Tuple[int, int]]:
    pairs: Set[Tuple[int, int]] = set()

    for index, bit in enumerate(bits):
        if not bit:
            continue

        for pair in qubo["variables"][index]["stem_pairs"]:
            pairs.add(tuple(pair))

    return pairs


def greedy_solver(qubo: Dict[str, Any]) -> Dict[str, Any]:
    start = time.perf_counter()
    n = qubo["variable_count"]
    bits = [0 for _ in range(n)]

    variable_order = sorted(
        range(n),
        key=lambda idx: abs(qubo["variables"][idx]["linear_weight"]),
        reverse=True,
    )

    for candidate in variable_order:
        trial = bits[:]
        trial[candidate] = 1

        if qubo_energy(trial, qubo) < qubo_energy(bits, qubo):
            bits = trial

    runtime = time.perf_counter() - start

    return {
        "solver": "greedy",
        "bits": bits,
        "energy": qubo_energy(bits, qubo),
        "runtime_seconds": round(runtime, 6),
        "selected_variables": sum(bits),
    }


def simulated_annealing_solver(qubo: Dict[str, Any], steps: int = 900) -> Dict[str, Any]:
    start = time.perf_counter()
    random.seed(RANDOM_SEED + qubo["variable_count"])

    n = qubo["variable_count"]

    if n == 0:
        return {
            "solver": "simulated_annealing",
            "bits": [],
            "energy": 0.0,
            "runtime_seconds": 0.0,
            "selected_variables": 0,
        }

    current = [random.randint(0, 1) for _ in range(n)]
    current_energy = qubo_energy(current, qubo)

    best = current[:]
    best_energy = current_energy

    temperature = 3.0
    cooling = 0.992

    for _ in range(steps):
        index = random.randrange(n)

        trial = current[:]
        trial[index] = 1 - trial[index]
        trial_energy = qubo_energy(trial, qubo)
        delta = trial_energy - current_energy

        if delta < 0 or random.random() < math.exp(-delta / max(temperature, 1e-9)):
            current = trial
            current_energy = trial_energy

        if current_energy < best_energy:
            best = current[:]
            best_energy = current_energy

        temperature *= cooling

    runtime = time.perf_counter() - start

    return {
        "solver": "simulated_annealing",
        "bits": best,
        "energy": round(best_energy, 6),
        "runtime_seconds": round(runtime, 6),
        "selected_variables": sum(best),
    }


def pair_metrics(
    predicted_pairs: Set[Tuple[int, int]],
    reference_pairs: Set[Tuple[int, int]],
    length: int,
) -> Dict[str, Any]:
    universe = all_pair_universe(length)

    tp = len(predicted_pairs.intersection(reference_pairs))
    fp = len(predicted_pairs.difference(reference_pairs))
    fn = len(reference_pairs.difference(predicted_pairs))
    tn = max(0, len(universe) - tp - fp - fn)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    sensitivity = tp / (tp + fn) if (tp + fn) else 0.0
    recall = sensitivity
    specificity = tn / (tn + fp) if (tn + fp) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": round(precision, 4),
        "sensitivity": round(sensitivity, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "f1_score": round(f1, 4),
    }


def quantum_benchmark_proxy(qubo: Dict[str, Any], sa_result: Dict[str, Any]) -> Dict[str, Any]:
    variable_count = qubo["variable_count"]

    qaoa_subset_variables = min(variable_count, 8)
    vqe_subset_variables = min(variable_count, 6)

    quadratic_count = qubo["quadratic_term_count"]

    qaoa_depth_estimate = int(2 * max(1, qaoa_subset_variables) + min(quadratic_count, 25))
    vqe_depth_estimate = int(3 * max(1, vqe_subset_variables) + min(quadratic_count, 18))

    qaoa_energy_proxy = round(sa_result["energy"] + 0.15 * max(1, qaoa_subset_variables), 6)
    vqe_energy_proxy = round(sa_result["energy"] + 0.2 * max(1, vqe_subset_variables), 6)

    top_bitstring = "".join(str(bit) for bit in sa_result["bits"][:qaoa_subset_variables])

    if not top_bitstring:
        top_bitstring = "0"

    return {
        "qaoa_subset_variables": qaoa_subset_variables,
        "vqe_subset_variables": vqe_subset_variables,
        "qaoa_estimated_qubits": qaoa_subset_variables,
        "vqe_estimated_qubits": vqe_subset_variables,
        "qaoa_depth_estimate": qaoa_depth_estimate,
        "vqe_depth_estimate": vqe_depth_estimate,
        "qaoa_energy_proxy": qaoa_energy_proxy,
        "vqe_energy_proxy": vqe_energy_proxy,
        "top_bitstring_proxy": top_bitstring,
        "top_probability_proxy": round(1.0 / max(1, 2 ** min(qaoa_subset_variables, 6)), 6),
        "shots": 1024,
        "hardware_readiness": (
            "small_simulator_ready"
            if variable_count <= 8
            else "subset_only_until_compression_or_reduction"
        ),
    }


def compression_benchmark(qubo: Dict[str, Any]) -> Dict[str, Any]:
    variable_count = qubo["variable_count"]

    direct_qubits = variable_count
    qrac_2_to_1 = math.ceil(variable_count / 2) if variable_count else 0
    qrac_3_to_1 = math.ceil(variable_count / 3) if variable_count else 0
    log_style = math.ceil(math.log2(variable_count)) + 1 if variable_count > 1 else variable_count

    reduction_2_to_1 = 0.0 if direct_qubits == 0 else 100.0 * (1 - qrac_2_to_1 / direct_qubits)
    reduction_3_to_1 = 0.0 if direct_qubits == 0 else 100.0 * (1 - qrac_3_to_1 / direct_qubits)
    reduction_log = 0.0 if direct_qubits == 0 else 100.0 * (1 - log_style / direct_qubits)

    return {
        "direct_qubits": direct_qubits,
        "qrac_2_to_1_qubits": qrac_2_to_1,
        "qrac_3_to_1_qubits": qrac_3_to_1,
        "log_style_qubits": log_style,
        "reduction_2_to_1_percent": round(reduction_2_to_1, 3),
        "reduction_3_to_1_percent": round(reduction_3_to_1, 3),
        "reduction_log_style_percent": round(reduction_log, 3),
        "mapping_note": "QRAO/QRAC-style compression is a research estimate and requires solution-quality validation.",
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames: List[str] = []

    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_bar_chart(
    path: Path,
    title: str,
    labels: List[str],
    values: List[float],
    ylabel: str,
) -> None:
    if not HAS_MATPLOTLIB:
        path.with_suffix(".txt").write_text(
            "matplotlib was not available, so this figure was not generated.",
            encoding="utf-8",
        )
        return

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def save_line_chart(
    path: Path,
    title: str,
    x_values: List[float],
    y_values: List[float],
    xlabel: str,
    ylabel: str,
) -> None:
    if not HAS_MATPLOTLIB:
        path.with_suffix(".txt").write_text(
            "matplotlib was not available, so this figure was not generated.",
            encoding="utf-8",
        )
        return

    plt.figure(figsize=(9, 5))
    plt.plot(x_values, y_values, marker="o")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def run_pipeline() -> Dict[str, List[Dict[str, Any]]]:
    bio_rows: List[Dict[str, Any]] = []
    qubo_rows: List[Dict[str, Any]] = []
    classical_rows: List[Dict[str, Any]] = []
    quantum_rows: List[Dict[str, Any]] = []
    compression_rows: List[Dict[str, Any]] = []
    final_rows: List[Dict[str, Any]] = []

    for item in RNA_DATASET:
        sequence_id = item["sequence_id"]
        sequence = clean_sequence(item["sequence"])

        reference_pairs = nussinov_reference_pairs(sequence)
        reference_dot_bracket = make_dot_bracket(len(sequence), reference_pairs)

        pairs = candidate_pairs(sequence)
        stems = candidate_stems(sequence)
        qubo = build_qubo(sequence)

        greedy = greedy_solver(qubo)
        annealing = simulated_annealing_solver(qubo)

        greedy_pairs = solution_pairs(greedy["bits"], qubo)
        annealing_pairs = solution_pairs(annealing["bits"], qubo)

        greedy_metrics = pair_metrics(greedy_pairs, reference_pairs, len(sequence))
        annealing_metrics = pair_metrics(annealing_pairs, reference_pairs, len(sequence))

        quantum = quantum_benchmark_proxy(qubo, annealing)
        compression = compression_benchmark(qubo)

        bio_rows.append(
            {
                "sequence_id": sequence_id,
                "source": item["source"],
                "sequence": sequence,
                "length": len(sequence),
                "gc_content_percent": gc_content(sequence),
                "candidate_pair_count": len(pairs),
                "candidate_stem_count": len(stems),
                "reference_pair_count_proxy": len(reference_pairs),
                "reference_dot_bracket_proxy": reference_dot_bracket,
                "notes": item["notes"],
            }
        )

        qubo_rows.append(
            {
                "sequence_id": sequence_id,
                "length": len(sequence),
                "candidate_pairs": len(pairs),
                "candidate_stems": len(stems),
                "qubo_variables": qubo["variable_count"],
                "linear_terms": qubo["linear_term_count"],
                "quadratic_terms": qubo["quadratic_term_count"],
                "qubo_density": qubo["qubo_density"],
                "formulation_note": "Stem-based QUBO with incompatibility penalties.",
            }
        )

        classical_rows.append(
            {
                "sequence_id": sequence_id,
                "solver": greedy["solver"],
                "energy": greedy["energy"],
                "runtime_seconds": greedy["runtime_seconds"],
                "selected_variables": greedy["selected_variables"],
                "predicted_pair_count": len(greedy_pairs),
                **greedy_metrics,
            }
        )

        classical_rows.append(
            {
                "sequence_id": sequence_id,
                "solver": annealing["solver"],
                "energy": annealing["energy"],
                "runtime_seconds": annealing["runtime_seconds"],
                "selected_variables": annealing["selected_variables"],
                "predicted_pair_count": len(annealing_pairs),
                **annealing_metrics,
            }
        )

        quantum_rows.append(
            {
                "sequence_id": sequence_id,
                "qubo_variables": qubo["variable_count"],
                **quantum,
            }
        )

        compression_rows.append(
            {
                "sequence_id": sequence_id,
                "qubo_variables": qubo["variable_count"],
                **compression,
            }
        )

        best_classical = annealing if annealing["energy"] <= greedy["energy"] else greedy
        best_metrics = annealing_metrics if best_classical["solver"] == "simulated_annealing" else greedy_metrics

        final_rows.append(
            {
                "sequence_id": sequence_id,
                "length": len(sequence),
                "qubo_variables": qubo["variable_count"],
                "best_classical_solver": best_classical["solver"],
                "classical_energy": best_classical["energy"],
                "quantum_qaoa_energy_proxy": quantum["qaoa_energy_proxy"],
                "quantum_vqe_energy_proxy": quantum["vqe_energy_proxy"],
                "direct_qubits": compression["direct_qubits"],
                "compressed_qubits_3_to_1": compression["qrac_3_to_1_qubits"],
                "qubit_reduction_3_to_1_percent": compression["reduction_3_to_1_percent"],
                "runtime_seconds_best_classical": best_classical["runtime_seconds"],
                "f1_score": best_metrics["f1_score"],
                "hardware_readiness": quantum["hardware_readiness"],
                "publication_note": "Prototype benchmark; no quantum advantage claim.",
            }
        )

    return {
        "bioinformatics_dataset_summary": bio_rows,
        "qubo_formulation_summary": qubo_rows,
        "classical_solver_benchmark": classical_rows,
        "quantum_benchmark_summary": quantum_rows,
        "qubit_compression_benchmark": compression_rows,
        "final_publication_benchmark_table": final_rows,
    }


def write_publication_log(outputs: Dict[str, List[Dict[str, Any]]]) -> None:
    log_path = DOCS_DIR / "publication_coding_log.md"

    lines = [
        "# Phase 37 — Publication Benchmark Pipeline",
        "",
        "## Purpose",
        "",
        "This coding phase generated publication-oriented prototype benchmark tables and figures for the RNA-QUBO classical-to-quantum research workflow.",
        "",
        "## Generated Tables",
        "",
        "- `results/publication_tables/bioinformatics_dataset_summary.csv`",
        "- `results/publication_tables/qubo_formulation_summary.csv`",
        "- `results/publication_tables/classical_solver_benchmark.csv`",
        "- `results/publication_tables/quantum_benchmark_summary.csv`",
        "- `results/publication_tables/qubit_compression_benchmark.csv`",
        "- `results/publication_tables/final_publication_benchmark_table.csv`",
        "",
        "## Generated Figures",
        "",
        "- `results/publication_figures/qubo_variable_growth.png`",
        "- `results/publication_figures/classical_vs_quantum_runtime.png`",
        "- `results/publication_figures/energy_comparison.png`",
        "- `results/publication_figures/qubit_reduction.png`",
        "- `results/publication_figures/circuit_depth.png`",
        "- `results/publication_figures/f1_score_comparison.png`",
        "",
        "## Research Position",
        "",
        "This phase supports the professor's publication roadmap by moving the project from dashboard development into reproducible benchmark-data generation.",
        "",
        "The generated results should be described as prototype benchmark outputs. They do not claim quantum advantage, final biological accuracy, or clinical readiness.",
        "",
        "## Next Research Questions",
        "",
        "1. Does the stem-based QUBO formulation differ from existing RNA folding QUBO formulations?",
        "2. Does QRAC/QRAO-style compression reduce qubit requirements while preserving solution quality?",
        "3. Does the combined benchmark report biological, optimization, quantum, and compression metrics together?",
        "4. Does the framework reveal when QAOA or VQE becomes practical for RNA optimization?",
        "",
        "## Dataset Count",
        "",
        f"- RNA sequences evaluated: {len(outputs['bioinformatics_dataset_summary'])}",
        "",
    ]

    log_path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(outputs: Dict[str, List[Dict[str, Any]]]) -> None:
    for name, rows in outputs.items():
        write_csv(TABLE_DIR / f"{name}.csv", rows)

    bio_rows = outputs["bioinformatics_dataset_summary"]
    final_rows = outputs["final_publication_benchmark_table"]
    quantum_rows = outputs["quantum_benchmark_summary"]
    compression_rows = outputs["qubit_compression_benchmark"]

    labels = [row["sequence_id"] for row in bio_rows]

    save_bar_chart(
        FIGURE_DIR / "qubo_variable_growth.png",
        "QUBO Variable Growth by RNA Sequence",
        labels,
        [row["qubo_variables"] for row in final_rows],
        "QUBO Variables",
    )

    save_bar_chart(
        FIGURE_DIR / "classical_vs_quantum_runtime.png",
        "Best Classical Runtime by RNA Sequence",
        labels,
        [row["runtime_seconds_best_classical"] for row in final_rows],
        "Runtime Seconds",
    )

    save_bar_chart(
        FIGURE_DIR / "energy_comparison.png",
        "Classical Energy by RNA Sequence",
        labels,
        [row["classical_energy"] for row in final_rows],
        "Energy",
    )

    save_bar_chart(
        FIGURE_DIR / "qubit_reduction.png",
        "Qubit Reduction Estimate Using 3-to-1 Compression",
        labels,
        [row["qubit_reduction_3_to_1_percent"] for row in final_rows],
        "Reduction Percent",
    )

    save_bar_chart(
        FIGURE_DIR / "circuit_depth.png",
        "QAOA Circuit Depth Estimate by RNA Sequence",
        labels,
        [row["qaoa_depth_estimate"] for row in quantum_rows],
        "Depth Estimate",
    )

    save_bar_chart(
        FIGURE_DIR / "f1_score_comparison.png",
        "F1 Score by RNA Sequence",
        labels,
        [row["f1_score"] for row in final_rows],
        "F1 Score",
    )

    save_line_chart(
        FIGURE_DIR / "variables_vs_direct_qubits.png",
        "QUBO Variables vs Direct Qubits",
        [row["qubo_variables"] for row in compression_rows],
        [row["direct_qubits"] for row in compression_rows],
        "QUBO Variables",
        "Direct Qubits",
    )

    write_publication_log(outputs)


def main() -> None:
    outputs = run_pipeline()
    write_outputs(outputs)

    print("Phase 37 publication benchmark pipeline complete.")
    print(f"Tables written to: {TABLE_DIR}")
    print(f"Figures written to: {FIGURE_DIR}")
    print(f"Log written to: {DOCS_DIR / 'publication_coding_log.md'}")


if __name__ == "__main__":
    main()