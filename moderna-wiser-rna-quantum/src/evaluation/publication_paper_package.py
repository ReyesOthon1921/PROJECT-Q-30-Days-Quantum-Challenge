from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
TABLE_DIR = ROOT / "results" / "publication_tables"

DOCS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def summarize_final_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "sequence_count": 0,
            "max_length": 0,
            "max_qubo_variables": 0,
            "avg_f1": 0.0,
            "avg_qubit_reduction": 0.0,
            "best_f1_sequence": "not available",
            "largest_qubo_sequence": "not available",
        }

    sequence_count = len(rows)
    max_length = max(safe_int(row.get("length")) for row in rows)
    max_qubo_variables = max(safe_int(row.get("qubo_variables")) for row in rows)

    avg_f1 = sum(safe_float(row.get("f1_score")) for row in rows) / sequence_count
    avg_qubit_reduction = (
        sum(safe_float(row.get("qubit_reduction_3_to_1_percent")) for row in rows)
        / sequence_count
    )

    best_f1_row = max(rows, key=lambda row: safe_float(row.get("f1_score")))
    largest_qubo_row = max(rows, key=lambda row: safe_int(row.get("qubo_variables")))

    return {
        "sequence_count": sequence_count,
        "max_length": max_length,
        "max_qubo_variables": max_qubo_variables,
        "avg_f1": round(avg_f1, 4),
        "avg_qubit_reduction": round(avg_qubit_reduction, 3),
        "best_f1_sequence": best_f1_row.get("sequence_id", "not available"),
        "largest_qubo_sequence": largest_qubo_row.get("sequence_id", "not available"),
    }


def make_paper_outline(summary: Dict[str, Any]) -> str:
    return f"""# Paper Outline

## Working Title

**A Bioinformatics-to-Quantum Benchmarking Framework for RNA Secondary Structure Prediction Using QUBO, QAOA, VQE, and Qubit-Compression Analysis**

## Paper Purpose

This paper presents a prototype research framework for RNA secondary-structure prediction and optimization. The project connects bioinformatics preprocessing, QUBO formulation, classical optimization, quantum algorithm simulation, qubit-compression analysis, hardware-readiness evaluation, and publication-style benchmark reporting.

The goal is not to claim quantum advantage. The goal is to create a reproducible framework that can test when RNA-QUBO problems become practical for classical, quantum, and qubit-compressed workflows.

## Proposed Paper Sections

### 1. Abstract

Briefly summarize the research problem, the proposed framework, the benchmark pipeline, and the main contribution.

### 2. Introduction

Introduce RNA secondary-structure prediction as an optimization problem. Explain why QUBO modeling is useful for connecting RNA folding problems to classical and quantum optimization methods.

### 3. Related Work

Cover RNA folding methods, ViennaRNA/RNAfold, QUBO formulations, QAOA, VQE, quantum annealing, NISQ limitations, and QRAC/QRAO-style qubit compression.

### 4. Research Gap

Explain that many works study RNA folding, QUBO, or quantum solvers separately. This project contributes a unified benchmark workflow that compares biological metrics, optimization metrics, quantum feasibility metrics, and qubit-compression metrics together.

### 5. Methodology

Explain the full pipeline:

RNA sequence → bioinformatics preprocessing → candidate pairs/stems → QUBO formulation → classical solvers → quantum benchmark proxy → qubit-compression estimates → final benchmark table.

### 6. Dataset and Preprocessing

Describe the RNA sequences used in the current prototype benchmark and explain sequence cleaning, GC-content calculation, candidate pair detection, candidate stem generation, and reference-pair proxy generation.

### 7. QUBO Formulation

Define the stem-based binary variables, objective function, linear weights, quadratic incompatibility penalties, and QUBO density.

### 8. Classical Benchmark

Describe greedy optimization and simulated annealing. Report runtime, energy, selected variables, predicted pairs, sensitivity, specificity, precision, recall, and F1-score.

### 9. Quantum Benchmark

Describe QAOA readiness, VQE readiness, circuit-depth estimates, qubit counts, top bitstring proxy, top probability proxy, and hardware-readiness classification.

### 10. Qubit Compression Layer

Compare direct encoding with 2-to-1 and 3-to-1 QRAC/QRAO-style compression estimates. Explain that compression can reduce qubit requirements but must be validated for solution quality.

### 11. Results

Report final benchmark outputs.

Current generated benchmark summary:

- RNA sequences evaluated: **{summary["sequence_count"]}**
- Maximum sequence length: **{summary["max_length"]}**
- Maximum QUBO variables: **{summary["max_qubo_variables"]}**
- Average F1-score: **{summary["avg_f1"]}**
- Average 3-to-1 qubit reduction estimate: **{summary["avg_qubit_reduction"]}%**
- Best F1 sequence: **{summary["best_f1_sequence"]}**
- Largest QUBO sequence: **{summary["largest_qubo_sequence"]}**

### 12. Discussion

Discuss the strengths and limitations of the framework. Emphasize that this is a prototype benchmark and does not claim quantum advantage.

### 13. Hardware Readiness

Discuss qubit-count requirements, circuit-depth limitations, NISQ constraints, simulator-first testing, and future IBM Quantum/Qiskit hardware testing.

### 14. Limitations

Explain current dataset size, reference-proxy limitations, simplified energy model, simulator-only quantum experiments, and the need to validate compression quality.

### 15. Conclusion and Future Work

Summarize the contribution and list future improvements: larger RNA datasets, stronger ViennaRNA comparison, additional classical solvers, noise simulation, real hardware testing, and improved QRAC/QRAO validation.
"""


def make_research_problem() -> str:
    return """# Research Problem

## Main Research Problem

RNA secondary-structure prediction is a biological optimization problem. The structure of an RNA molecule depends on which bases pair with each other and how those pairings form stems, loops, and other secondary-structure features.

Traditional RNA folding tools usually focus on thermodynamic modeling and minimum free energy prediction. Quantum and quantum-inspired methods require a different representation: the problem must be translated into a binary optimization model such as QUBO or Ising form.

The research problem for this project is:

**Can RNA secondary-structure prediction be represented as a QUBO problem and evaluated through a unified classical, quantum, and qubit-compression benchmarking framework?**

## Why This Problem Matters

RNA structure prediction is important because RNA structure affects biological function. For mRNA design, RNA therapeutics, and computational biology, predicting stable and meaningful RNA secondary structures is a valuable research direction.

Quantum computing introduces a possible future path for optimization, but current quantum hardware is limited by:

- Qubit count
- Circuit depth
- Noise
- Connectivity
- Gate errors
- Measurement uncertainty

Because of these limitations, the project does not claim quantum advantage. Instead, it asks a more careful research question:

**What can be learned by building a transparent benchmark that compares RNA-QUBO problems across classical solvers, quantum algorithm prototypes, and qubit-compression estimates?**

## Core Research Questions

1. Does the stem-based QUBO formulation differ from existing RNA folding QUBO formulations?
2. Can QRAC/QRAO-style qubit compression reduce qubit requirements while maintaining solution quality?
3. Can biological metrics, optimization metrics, quantum metrics, and compression metrics be reported together in one benchmark?
4. Can the framework reveal when QAOA or VQE becomes practical for RNA optimization?
5. What are the current limitations of using NISQ-era quantum methods for RNA-QUBO problems?

## Research Position

This project should be described as a prototype benchmark and feasibility study.

It is not a final biological prediction model.

It is not a clinical tool.

It does not prove quantum advantage.

The contribution is the integrated workflow:

**RNA sequence → bioinformatics preprocessing → QUBO formulation → classical benchmark → quantum benchmark → qubit compression → hardware readiness → publication results.**
"""


def make_methodology() -> str:
    return """# Methodology

## Overview

The methodology follows an end-to-end pipeline for RNA secondary-structure optimization using classical, quantum, and qubit-compression analysis.

The full workflow is:

**RNA sequence → bioinformatics preprocessing → candidate base pairs → candidate stems → QUBO formulation → classical optimization → quantum benchmark proxy → qubit compression → final publication benchmark table.**

## 1. Dataset Preparation

The current prototype uses a controlled set of RNA sequences. Each sequence is cleaned and converted into a valid RNA alphabet containing only:

- A
- U
- G
- C

Any thymine value is converted to uracil so the pipeline remains RNA-based.

## 2. Bioinformatics Preprocessing

For each sequence, the pipeline calculates:

- Sequence length
- GC-content percentage
- Candidate base pairs
- Candidate stems
- Reference-pair proxy
- Dot-bracket proxy structure

Candidate base pairs are generated using common RNA base-pair rules:

- A-U
- U-A
- G-C
- C-G
- G-U
- U-G

## 3. Reference-Pair Proxy

A simplified Nussinov-style dynamic programming method is used to generate a reference-pair proxy for prototype evaluation.

This does not replace ViennaRNA or RNAfold. It provides a controlled internal reference so that sensitivity, specificity, precision, recall, and F1-score can be computed during early benchmark development.

## 4. Candidate Stem Generation

Candidate stems are generated from compatible base pairs. A stem is treated as one or more stacked or related base-pair decisions.

This helps reduce the problem from individual pair decisions into stem-level decisions.

## 5. QUBO Formulation

The QUBO model uses candidate stems as binary decision variables.

Each variable represents whether a candidate stem is selected:

- 1 means selected
- 0 means not selected

The QUBO contains:

- Linear terms rewarding stronger stems
- Quadratic penalty terms discouraging incompatible stems
- QUBO density measurement
- Variable count
- Linear term count
- Quadratic term count

The QUBO formulation is currently a prototype stem-based model.

## 6. Classical Optimization

Two classical solvers are currently benchmarked:

### Greedy Solver

The greedy solver selects variables when they improve the QUBO energy.

### Simulated Annealing

The simulated annealing solver explores possible binary assignments using probabilistic acceptance and cooling.

Classical metrics include:

- Energy
- Runtime
- Selected variables
- Predicted pair count
- Sensitivity
- Specificity
- Precision
- Recall
- F1-score

## 7. Quantum Benchmark Proxy

The quantum benchmark layer estimates QAOA and VQE readiness using the QUBO variable count and quadratic-term structure.

The current benchmark records:

- QAOA subset variables
- VQE subset variables
- Estimated qubits
- Estimated circuit depth
- Energy proxy
- Top bitstring proxy
- Top probability proxy
- Shot count
- Hardware-readiness label

This is a simulator-readiness and feasibility layer. It does not claim real quantum advantage.

## 8. Qubit Compression Benchmark

The qubit-compression layer compares direct encoding with compressed estimates.

The benchmark includes:

- Direct one-variable-per-qubit encoding
- 2-to-1 QRAC-style estimate
- 3-to-1 QRAC/QRAO-style estimate
- Log-style qubit estimate
- Qubit reduction percentage
- Mapping notes and limitations

This layer studies whether qubit requirements can be reduced, but solution quality must still be validated.

## 9. Final Publication Benchmark Table

The final benchmark table combines:

- Sequence ID
- Sequence length
- QUBO variables
- Best classical solver
- Classical energy
- QAOA energy proxy
- VQE energy proxy
- Direct qubits
- Compressed qubits
- Qubit reduction percentage
- Runtime
- F1-score
- Hardware-readiness notes

This table is designed to support the results section of the paper.

## 10. Reproducibility

All benchmark tables and figures are generated by:

`src/evaluation/publication_benchmark_pipeline.py`

The paper package documents are generated by:

`src/evaluation/publication_paper_package.py`

This keeps the workflow reproducible and version-controlled.
"""


def make_results_summary(summary: Dict[str, Any], final_rows: List[Dict[str, Any]]) -> str:
    table_lines = [
        "| Sequence | Length | QUBO Variables | Best Solver | Classical Energy | Direct Qubits | 3-to-1 Qubits | F1-score | Hardware Readiness |",
        "|---|---:|---:|---|---:|---:|---:|---:|---|",
    ]

    for row in final_rows:
        table_lines.append(
            f"| {row.get('sequence_id', '')} "
            f"| {row.get('length', '')} "
            f"| {row.get('qubo_variables', '')} "
            f"| {row.get('best_classical_solver', '')} "
            f"| {row.get('classical_energy', '')} "
            f"| {row.get('direct_qubits', '')} "
            f"| {row.get('compressed_qubits_3_to_1', '')} "
            f"| {row.get('f1_score', '')} "
            f"| {row.get('hardware_readiness', '')} |"
        )

    table_text = "\n".join(table_lines)

    return f"""# Results Summary

## Phase 37 Benchmark Output Summary

The first publication benchmark pipeline generated prototype results for RNA secondary-structure optimization using bioinformatics preprocessing, QUBO formulation, classical optimization, quantum benchmark proxy metrics, and qubit-compression estimates.

## High-Level Results

- RNA sequences evaluated: **{summary["sequence_count"]}**
- Maximum sequence length: **{summary["max_length"]}**
- Maximum QUBO variables: **{summary["max_qubo_variables"]}**
- Average F1-score: **{summary["avg_f1"]}**
- Average 3-to-1 qubit reduction estimate: **{summary["avg_qubit_reduction"]}%**
- Best F1 sequence: **{summary["best_f1_sequence"]}**
- Largest QUBO sequence: **{summary["largest_qubo_sequence"]}**

## Generated Result Tables

The following CSV files were generated:

- `results/publication_tables/bioinformatics_dataset_summary.csv`
- `results/publication_tables/qubo_formulation_summary.csv`
- `results/publication_tables/classical_solver_benchmark.csv`
- `results/publication_tables/quantum_benchmark_summary.csv`
- `results/publication_tables/qubit_compression_benchmark.csv`
- `results/publication_tables/final_publication_benchmark_table.csv`

## Generated Figures

The following figures were generated:

- `results/publication_figures/qubo_variable_growth.png`
- `results/publication_figures/classical_vs_quantum_runtime.png`
- `results/publication_figures/energy_comparison.png`
- `results/publication_figures/qubit_reduction.png`
- `results/publication_figures/circuit_depth.png`
- `results/publication_figures/f1_score_comparison.png`
- `results/publication_figures/variables_vs_direct_qubits.png`

## Final Publication Benchmark Table

{table_text}

## Interpretation

The current results should be interpreted as prototype benchmark outputs.

They show that the framework can generate unified metrics across:

- Bioinformatics preprocessing
- QUBO formulation
- Classical solver performance
- Quantum feasibility estimates
- Qubit-compression estimates
- Hardware-readiness classification

The next research task is to validate these outputs against stronger external RNA folding tools and larger datasets.
"""


def make_novelty_questions() -> str:
    return """# Novelty Questions

This document organizes the key research questions from the professor into paper-ready form.

## Question 1

### Does the QUBO formulation differ from existing RNA folding formulations?

Current answer:

The project uses a stem-based QUBO formulation where candidate stems are represented as binary decision variables. Linear terms reward favorable stems, while quadratic penalty terms discourage incompatible stems such as overlapping or crossing structures.

This must be compared against existing RNA-QUBO and RNA quantum annealing formulations in the literature.

Evidence needed:

- Literature table comparing variable definitions
- Literature table comparing constraints
- Comparison of pair-based vs stem-based modeling
- Comparison of QUBO term growth
- Discussion of pseudoknot or incompatibility handling

## Question 2

### Does the variable-compression strategy reduce qubit requirements while maintaining solution quality?

Current answer:

The project currently estimates qubit reduction using direct encoding, 2-to-1 QRAC-style compression, 3-to-1 QRAC/QRAO-style compression, and log-style qubit estimates.

The project can show qubit-count reduction estimates, but it must still validate whether compressed mappings preserve solution quality.

Evidence needed:

- Direct qubit count
- Compressed qubit count
- Reduction percentage
- Energy comparison
- F1-score comparison
- Mapping error or approximation-quality discussion

Important wording:

Compression is currently a research direction and benchmark extension, not proof of improved RNA folding performance.

## Question 3

### Does the benchmarking include datasets or evaluation metrics not previously reported together?

Current answer:

The project combines biological metrics, optimization metrics, quantum metrics, and compression metrics into one final benchmark table.

Metrics include:

- Sequence length
- GC content
- Candidate pairs
- Candidate stems
- QUBO variables
- Linear and quadratic terms
- QUBO density
- Runtime
- Energy
- Sensitivity
- Specificity
- Precision
- Recall
- F1-score
- Estimated qubits
- Circuit-depth estimates
- Bitstring proxy
- Qubit reduction percentage
- Hardware-readiness label

Evidence needed:

- Final publication benchmark table
- Comparison to what previous papers report
- Clear statement of which metrics are combined in this project

## Question 4

### Does the framework reveal new insights into when QAOA or VQE becomes practical for RNA optimization?

Current answer:

The framework estimates QAOA and VQE practicality by tracking QUBO variable count, estimated qubits, circuit-depth estimates, runtime, energy proxy values, bitstring output, and hardware-readiness labels.

The current results are simulator and proxy-based. The next step is to test small cases with actual Qiskit circuits and compare runtime, depth, and measured bitstring quality.

Evidence needed:

- QAOA circuit depth by variable count
- VQE circuit depth by variable count
- Hardware-readiness table
- Qubit-count threshold discussion
- NISQ limitation discussion
- Noise simulation in future work

## Proposed Novelty Statement

This project contributes an end-to-end bioinformatics-to-quantum benchmarking framework for RNA secondary-structure optimization. The framework connects RNA preprocessing, stem-based QUBO formulation, classical solver benchmarking, QAOA/VQE feasibility analysis, qubit-compression estimates, and hardware-readiness evaluation into one reproducible workflow.

The novelty is the integrated benchmark framework, not a claim of quantum advantage.
"""


def make_limitations() -> str:
    return """# Limitations

## 1. Prototype Dataset

The current dataset is small and controlled. It includes demonstration and synthetic RNA sequences for early benchmark development.

Future work must include larger and more biologically meaningful RNA datasets.

## 2. Reference Structure Limitation

The current benchmark uses an internal Nussinov-style reference-pair proxy. This is useful for early testing but does not replace established RNA folding tools.

Future work should compare against:

- ViennaRNA
- RNAfold
- experimentally supported RNA structures
- curated RNA secondary-structure datasets

## 3. Simplified Energy Model

The current QUBO energy model uses simplified stem scores and incompatibility penalties.

Future work should improve the energy model using more realistic RNA thermodynamic parameters.

## 4. QUBO Formulation Still Needs Literature Comparison

The stem-based QUBO formulation must be compared carefully against existing RNA-QUBO and quantum annealing RNA papers.

The paper should not claim novelty in QUBO formulation until the literature comparison is completed.

## 5. Quantum Results Are Simulator/Proxy Results

The current quantum layer includes QAOA/VQE readiness, depth estimates, energy proxies, and circuit-style benchmarking.

This does not prove real quantum advantage.

Future work should include:

- Real Qiskit circuit execution for small instances
- Noise models
- Hardware backend analysis
- Real IBM Quantum experiments when feasible

## 6. Qubit Compression Is Not Yet Validated

The qubit-compression layer estimates qubit reduction using QRAC/QRAO-style mappings.

However, reducing qubits does not automatically mean the solution quality is preserved.

Future work must test whether compressed representations maintain:

- Energy quality
- Pair prediction quality
- F1-score
- Approximation ratio
- Recoverability of useful bitstrings

## 7. Statistical Power Is Limited

Because the current benchmark dataset is small, statistical conclusions are limited.

The paper should describe the current work as a feasibility and prototype benchmark study.

## 8. No Clinical or Production Claim

This project is not a clinical RNA prediction tool.

It is not a production mRNA design system.

It is not claiming biological validation for therapeutic use.

## 9. No Quantum Advantage Claim

The project should clearly state:

**This work does not claim quantum advantage.**

The contribution is the integrated framework and benchmark pipeline.

## 10. Future Work

Future work includes:

- Larger datasets
- Stronger RNAfold/ViennaRNA validation
- Better thermodynamic modeling
- Additional classical solvers
- Real QAOA/VQE circuit experiments
- Noise simulation
- Hardware testing
- Stronger QRAC/QRAO validation
- Formal journal manuscript preparation
"""


def write_doc(filename: str, content: str) -> None:
    path = DOCS_DIR / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")


def main() -> None:
    final_rows = read_csv_rows(TABLE_DIR / "final_publication_benchmark_table.csv")
    summary = summarize_final_rows(final_rows)

    write_doc("paper_outline.md", make_paper_outline(summary))
    write_doc("research_problem.md", make_research_problem())
    write_doc("methodology.md", make_methodology())
    write_doc("results_summary.md", make_results_summary(summary, final_rows))
    write_doc("novelty_questions.md", make_novelty_questions())
    write_doc("limitations.md", make_limitations())

    print("Phase 38 publication paper package complete.")
    print(f"Docs written to: {DOCS_DIR}")
    print("Created:")
    print("- docs/paper_outline.md")
    print("- docs/research_problem.md")
    print("- docs/methodology.md")
    print("- docs/results_summary.md")
    print("- docs/novelty_questions.md")
    print("- docs/limitations.md")


if __name__ == "__main__":
    main()