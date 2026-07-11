# Results Summary

## Phase 37 Benchmark Output Summary

The first publication benchmark pipeline generated prototype results for RNA secondary-structure optimization using bioinformatics preprocessing, QUBO formulation, classical optimization, quantum benchmark proxy metrics, and qubit-compression estimates.

## High-Level Results

- RNA sequences evaluated: **6**
- Maximum sequence length: **44**
- Maximum QUBO variables: **30**
- Average F1-score: **0.5814**
- Average 3-to-1 qubit reduction estimate: **63.195%**
- Best F1 sequence: **RNA_03_medium_control**
- Largest QUBO sequence: **RNA_01_demo**

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

| Sequence | Length | QUBO Variables | Best Solver | Classical Energy | Direct Qubits | 3-to-1 Qubits | F1-score | Hardware Readiness |
|---|---:|---:|---|---:|---:|---:|---:|---|
| RNA_01_demo | 44 | 30 | simulated_annealing | -31.0 | 30 | 10 | 0.5714 | subset_only_until_compression_or_reduction |
| RNA_02_short_hairpin | 9 | 4 | simulated_annealing | -7.0 | 4 | 2 | 0.75 | small_simulator_ready |
| RNA_03_medium_control | 15 | 9 | simulated_annealing | -12.0 | 9 | 3 | 1.0 | subset_only_until_compression_or_reduction |
| RNA_04_gc_rich | 13 | 8 | simulated_annealing | -18.0 | 8 | 3 | 1.0 | small_simulator_ready |
| RNA_05_balanced | 21 | 15 | simulated_annealing | -14.0 | 15 | 5 | 0.1667 | subset_only_until_compression_or_reduction |
| RNA_06_longer_control | 27 | 30 | simulated_annealing | -17.0 | 30 | 10 | 0.0 | subset_only_until_compression_or_reduction |

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

<!-- PHASE41_EXACT_VALIDATION_INTEGRATION -->
# Phase 41 Update — Exact Validation Integration

Phase 41 integrated the exact-validation outputs into the final benchmark layer.

The final publication benchmark now includes exact small-instance ground truth, including exact minimum energy, assignment count, feasibility, best bitstring, energy audit terms, and QUBO-to-Ising coefficient summaries.

This strengthens the results section because the benchmark now connects:

RNA/QUBO formulation  
→ exact small-instance validation  
→ energy audit  
→ QUBO-to-Ising mapping  
→ classical/quantum/compression benchmark context.

Important interpretation:

This does not prove quantum advantage. It makes the benchmark more auditable and gives a stronger validation foundation before interpreting QAOA, VQE, hardware-readiness, or QRAO compression outputs.

<!-- PHASE43_EXACT_VALIDATION_FIGURES -->
# Phase 43 Update — Exact Validation Publication Figures

Phase 43 generated publication-ready figures from the exact-validation layer.

Generated figures:

- Exact minimum QUBO energy by RNA sequence
- Exact enumeration assignment growth
- QUBO energy decomposition
- QUBO-to-Ising coefficient counts

These figures strengthen the paper results section by turning the exact-validation CSV outputs into visual evidence.

Safe interpretation:

The figures show exact small-instance validation and auditability. They do not claim quantum advantage or final biological validation.
