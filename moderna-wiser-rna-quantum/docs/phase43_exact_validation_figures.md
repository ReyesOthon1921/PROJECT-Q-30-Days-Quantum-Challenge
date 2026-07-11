# Phase 43 — Exact Validation Publication Figures

## Purpose

Phase 43 converts the exact-validation tables into publication-ready figures.

The goal is to make the exact-validation layer easier to interpret visually for the paper, dashboard, and professor review.

## Input Tables

- `results/publication_tables/exact_validation_results.csv`
- `results/publication_tables/qubo_energy_audit_summary.csv`
- `results/publication_tables/qubo_to_ising_coefficients.csv`
- `results/publication_tables/exact_validation_integrated_summary.csv`

## Generated Figures

- `results/publication_figures/exact_minimum_energy.png`
- `results/publication_figures/exact_assignment_growth.png`
- `results/publication_figures/exact_energy_decomposition.png`
- `results/publication_figures/ising_coefficient_counts.png`

## Summary

- Exact-validation sequences plotted: 4
- Energy audit rows plotted: 4
- QUBO-to-Ising coefficient rows read: 275
- Total exact-enumeration assignments checked: 70400
- Best exact minimum energy: -13.0
- Worst exact minimum energy: -4.5
- Total Ising linear fields: 45
- Total Ising couplings: 226

## Figure Meanings

### Exact Minimum Energy

Shows the exact minimum QUBO energy found for each small RNA validation instance.

### Assignment Growth

Shows how exact enumeration grows with QUBO variable count. The y-axis uses a logarithmic scale because bitstring assignments grow exponentially.

### Energy Decomposition

Separates the exact optimum energy into linear reward, overlap penalty, crossing penalty, and interaction terms.

### Ising Coefficient Counts

Shows the number of constant, linear-field, and coupling terms produced by the QUBO-to-Ising conversion.

## Safe Interpretation

These figures support auditability and exact small-instance validation.

They do not claim quantum advantage, final biological accuracy, or production-level RNA folding performance.
