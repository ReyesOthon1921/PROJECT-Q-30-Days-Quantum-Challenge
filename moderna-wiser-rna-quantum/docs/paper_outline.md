# Paper Outline

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

- RNA sequences evaluated: **6**
- Maximum sequence length: **44**
- Maximum QUBO variables: **30**
- Average F1-score: **0.5814**
- Average 3-to-1 qubit reduction estimate: **63.195%**
- Best F1 sequence: **RNA_03_medium_control**
- Largest QUBO sequence: **RNA_01_demo**

### 12. Discussion

Discuss the strengths and limitations of the framework. Emphasize that this is a prototype benchmark and does not claim quantum advantage.

### 13. Hardware Readiness

Discuss qubit-count requirements, circuit-depth limitations, NISQ constraints, simulator-first testing, and future IBM Quantum/Qiskit hardware testing.

### 14. Limitations

Explain current dataset size, reference-proxy limitations, simplified energy model, simulator-only quantum experiments, and the need to validate compression quality.

### 15. Conclusion and Future Work

Summarize the contribution and list future improvements: larger RNA datasets, stronger ViennaRNA comparison, additional classical solvers, noise simulation, real hardware testing, and improved QRAC/QRAO validation.
