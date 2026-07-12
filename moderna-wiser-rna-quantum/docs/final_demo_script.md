# Final Demo Script — 3 to 5 Minutes

## 0:00–0:30 — Project purpose

Say:

> This project explores mRNA secondary-structure prediction as an optimization problem. The goal is not to claim quantum advantage, but to build a reproducible RNA-QUBO benchmark framework that connects classical RNA folding, QUBO construction, solver baselines, and quantum-readiness analysis.

Show:

- `README.md`
- `docs/final_submission_summary.md`

## 0:30–1:15 — Pipeline overview

Say:

> The pipeline starts with an RNA sequence, generates candidate pairs and stems, builds a stem-based QUBO, solves it with classical baselines, reconstructs a dot-bracket structure, and saves a reproducible report.

Show:

- `src/evaluation/strict_classical_pipeline.py`
- `results/classical_foundation/final_submission_single_sequence/experiment_report.md`

## 1:15–2:00 — 12-sequence benchmark

Say:

> The project includes a final 12-sequence batch benchmark. This proves the pipeline is not only a one-off example.

Show:

- `results/classical_foundation_batch/final_submission_12_sequence_check/batch_summary.csv`
- `results/classical_foundation_batch/final_submission_12_sequence_check/batch_report.md`

## 2:00–2:45 — QUBO and validation

Say:

> The QUBO layer is traceable and includes exact small-instance validation, energy audits, and QUBO-to-Ising conversion for quantum-readiness.

Show:

- `docs/mathematical_formulation.md`
- `results/publication_tables/exact_validation_results.csv`
- `results/publication_tables/qubo_energy_audit_summary.csv`

## 2:45–3:30 — Quantum readiness and scaling

Say:

> After the classical QUBO is validated, the project estimates quantum-readiness through QAOA/VQE prototypes, circuit comparison, qubit estimates, scaling analysis, and graph-aware compression notes.

Show:

- `docs/quantum_circuit_report.md`
- `results/publication_tables/quantum_benchmark_summary.csv`
- `results/publication_tables/graph_aware_qrao_summary.csv`
- `results/publication_figures/`

## 3:30–4:30 — Limitations and safe claims

Say:

> The project is careful not to overclaim. It does not claim quantum advantage, clinical accuracy, or final biological validation. ViennaRNA MFE and QUBO energy are different scoring systems.

Show:

- `docs/final_limitations_and_safe_claims.md`

## 4:30–5:00 — Final close

Say:

> The final contribution is a reproducible research prototype and benchmark framework that prepares RNA-QUBO optimization for future stronger validation and quantum experiments.
