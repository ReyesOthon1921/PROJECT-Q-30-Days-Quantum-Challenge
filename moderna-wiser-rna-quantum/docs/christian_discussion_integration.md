# Christian St. Louis Mathematical Discussion Integration

## Purpose

This document records how Christian St. Louis's mathematical discussion draft is being integrated into the project.

## Contribution Note

Christian St. Louis provided a mathematical discussion draft and research feedback focused on improving the auditability of the RNA Stem-QUBO framework.

His contribution helped clarify the need for:

- explicit variable definitions,
- coefficient interpretation,
- penalty calibration,
- QUBO-to-Ising conversion,
- exact small-instance validation,
- energy auditing,
- graph-aware QRAO compression analysis.

This input is being used as discussion guidance and a comparison framework. It is not being treated as a replacement for the implemented model.

## Integration Decision

The project will add a new Phase 40 focused on mathematical traceability and exact validation.

The goal is to make the QUBO layer auditable before expanding claims about QAOA, VQE, or QRAO compression.

## Main Ideas Adopted

### 1. Pair-Based Reference Model

A pair-based model is useful as an audit layer because it makes base-pair constraints explicit.

### 2. Stem-Based Main QUBO

The project will continue using a stem-based QUBO as the main computational model.

### 3. Explicit Coefficients

The project will define and export linear coefficients, overlap penalties, crossing penalties, and optional interaction terms.

### 4. Penalty Calibration

The project will document why penalties are chosen and later test penalty sensitivity.

### 5. QUBO-to-Ising Conversion

The project will document the exact mapping from binary QUBO variables to Ising spin variables for quantum cost Hamiltonians.

### 6. Exact Enumeration

Small QUBO instances will be solved exactly by enumerating all bitstrings.

### 7. Energy Audit

The project will export term-by-term energy contributions.

### 8. Graph-Aware QRAO

The QRAO layer should use the QUBO interaction graph to avoid packing interacting variables into the same qubit.

## Safe Collaboration Wording

Christian St. Louis contributed mathematical discussion guidance and formulation feedback. The final implementation, validation, and publication claims must still be reconciled with the code, professor guidance, existing RNA-QUBO literature, and benchmark results.
