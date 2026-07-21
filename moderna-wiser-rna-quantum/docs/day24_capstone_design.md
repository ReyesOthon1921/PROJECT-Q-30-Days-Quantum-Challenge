# Day 24 Capstone Design — RNAQ Labs

## Project title
RNAQ Labs: Quantum Decision Intelligence for RNA Design Optimization

## Purpose
Design a three-minute MVP workflow that makes the RNA-QUBO project easy to demo to challenge reviewers, professors, investors, and early collaborators.

## System architecture
1. User interface layer: guided input, sample sequences, audience mode, result cards.
2. RNA processing layer: sequence validation, candidate base-pair generation, candidate stem generation.
3. QUBO optimization layer: candidate stems become binary variables; conflicts become quadratic penalties.
4. Graph diagnostics layer: QUBO variables become graph nodes; conflicts become graph edges.
5. Validation layer: exact validation for small cases; solver comparison for larger cases.
6. Quantum-readiness layer: QUBO-to-Ising, QAOA/VQE readiness, qubit/compression estimates.
7. Decision intelligence layer: user-facing recommendation, risk explanation, safe claim, and next milestone.

## Three-minute MVP flow
RNA sequence input -> validation -> candidate pairs -> candidate stems -> QUBO variables -> graph conflicts -> risk label -> solver path -> report.

## Safe claim
This is a computational benchmark and decision-intelligence prototype. It does not claim quantum advantage, clinical accuracy, or final biological validation.
