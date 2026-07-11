# Phase 41 — Exact Validation Integration Into Final Benchmark

## Purpose

Phase 41 integrates the exact-validation layer back into the final publication benchmark.

The final benchmark now connects the earlier publication benchmark outputs with exact small-instance ground truth.

## Inputs

- `results/publication_tables/final_publication_benchmark_table.csv`
- `results/publication_tables/exact_validation_results.csv`
- `results/publication_tables/qubo_energy_audit_summary.csv`
- `results/publication_tables/qubo_to_ising_coefficients.csv`

## Outputs

- `results/publication_tables/final_publication_benchmark_table.csv`
- `results/publication_tables/final_publication_benchmark_table_pre_phase41_backup.csv`
- `results/publication_tables/final_publication_benchmark_with_exact_validation.csv`
- `results/publication_tables/exact_validation_integrated_summary.csv`
- `docs/phase41_exact_validation_integration.md`

## What Changed

The final publication benchmark now includes Phase 41 columns for:

- exact ground-truth availability,
- exact sequence ID,
- assignment count,
- exact minimum energy,
- degenerate minimum count,
- best bitstring,
- feasibility,
- decoded dot-bracket structure,
- decoded base pairs,
- linear energy,
- overlap penalty energy,
- crossing penalty energy,
- total QUBO energy,
- QUBO-to-Ising constant offset,
- Ising linear-field count,
- Ising coupling count,
- Ising coefficient ranges.

## Row Counts

- Original benchmark rows loaded: 6
- Exact-validation rows loaded: 4
- Integrated benchmark rows written: 10

## Research Meaning

This phase strengthens the research paper because the benchmark no longer only reports classical, quantum, and compression outputs.

It now also includes exact small-instance ground truth.

This helps separate QUBO validity from biological accuracy and gives a stronger foundation before interpreting QAOA, VQE, hardware-readiness, or QRAO compression layers.

## Safe Claim

This is still a prototype benchmark and feasibility framework.

The project does not claim quantum advantage, clinical accuracy, final biological validation, or proven compression improvement.

The contribution is the integrated and auditable bioinformatics-to-quantum benchmark workflow.
