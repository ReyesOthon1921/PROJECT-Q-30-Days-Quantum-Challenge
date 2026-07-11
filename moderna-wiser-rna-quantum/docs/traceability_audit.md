# Phase 40 — Traceability Audit

## Purpose

This document defines how the project will audit every part of the RNA Stem-QUBO model.

The audit standard is:

Base pair -> stem -> variable -> coefficient -> assumption -> QUBO energy -> decoded structure -> validation result.

## Why This Matters

The project already has a dashboard, QUBO builder, classical solvers, quantum prototypes, compression estimates, and publication tables.

The next requirement is mathematical auditability.

The research paper should not only show that the code runs. It should show why every term exists and how every result can be reproduced.

## Traceability Table

The file `results/publication_tables/stem_traceability_table.csv` should record:

- sequence ID
- sequence
- stem variable name
- variable index
- stem length
- base-pair positions
- base-pair identities
- linear coefficient
- stem score
- modeling assumption
- overlap conflicts
- crossing conflicts
- total conflict count

## Conflict Table Logic

A selected pair of stems is infeasible if:

1. the stems overlap by sharing a nucleotide, or
2. the stems create a forbidden crossing pattern.

The current model treats both as hard structural conflicts.

## Energy Audit

The file `results/publication_tables/qubo_energy_audit.csv` should record:

- sequence ID
- exact best bitstring
- term type
- variable or variable pair
- coefficient
- whether the term is active
- contribution to total energy
- reason or assumption

## Exact Validation Table

The file `results/publication_tables/exact_validation_results.csv` should record:

- sequence ID
- sequence length
- variable count
- assignment count
- exact minimum energy
- degenerate minimum count
- best bitstring
- selected stems
- decoded pairs
- dot-bracket structure
- feasibility
- exact validation note

## Interpretation Rule

QUBO validity and biological accuracy must be separated.

QUBO validity asks:

- Did the QUBO objective enforce the intended mathematical constraints?
- Did exact enumeration find a feasible optimum?
- Are conflicts penalized correctly?

Biological accuracy asks:

- Does the predicted structure match RNAfold, ViennaRNA, experimental structures, or curated references?

The current phase focuses on QUBO validity and auditability first.
