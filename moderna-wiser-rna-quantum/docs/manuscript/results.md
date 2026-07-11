# 4. Results

The project currently produces tables, figures, documentation, and a live dashboard supporting the RNA-QUBO workflow.

## 4.1 Dataset Readiness

The current validation dataset tracks 8 RNA sequences across exact-validation and bioinformatics-expansion groups.

## 4.2 Exact Validation

The exact-validation layer currently includes 4 small RNA-QUBO instances.

Across these instances, exact enumeration checked 70400 total bitstring assignments.

The best exact minimum QUBO energy observed is -13.0.

The exact-validation tables include exact minimum energy, degenerate minima count, best bitstring, feasibility, decoded base pairs, dot-bracket output, and energy audit terms.

## 4.3 Energy Audit

The QUBO energy audit separates the exact optimum into linear stem rewards, overlap penalties, crossing penalties, compatible interaction terms, and total energy.

## 4.4 QUBO-to-Ising Mapping

The project exports QUBO-to-Ising coefficients, including constant offsets, linear fields, and pairwise couplings.

## 4.5 Graph-Aware QRAO Compression

The graph-aware QRAO validation layer analyzes 4 exact-validation sequences.

4 graph-aware QRAO rows currently pass the no-same-qubit conflict check.

This confirms the mapping logic avoids assigning interacting QUBO variables to the same compressed qubit under the tested packing rule.

## 4.6 Figures

The current figure package includes scaling plots, quantum benchmark plots, exact-validation figures, and graph-aware QRAO figures.
