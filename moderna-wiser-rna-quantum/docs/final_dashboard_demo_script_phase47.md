# Final Dashboard Demo Script — Phase 47

## Goal

Use this script to explain the project clearly during professor review or a research demo.

## 1. Opening

This project is an RNA-QUBO quantum research prototype. It studies how RNA secondary-structure prediction can be represented as an optimization problem and evaluated through classical solvers, quantum-readiness modules, exact validation, and compression analysis.

## 2. Dashboard Link

https://moderna-wiser-rna-quantum.onrender.com

## 3. Demo Flow

### Step 1 — RNA Input

Show the RNA sequence input and explain that the pipeline starts with cleaned RNA sequences.

### Step 2 — Candidate Pairs and Stems

Explain that candidate base pairs and candidate stems become the structural building blocks for the QUBO model.

### Step 3 — Stem-Based QUBO

Explain that each candidate stem becomes a binary variable. Linear terms reward favorable stems, while quadratic terms penalize invalid combinations.

### Step 4 — Classical Solvers

Show greedy and simulated annealing as baseline solvers.

### Step 5 — Quantum Readiness

Explain QAOA/VQE readiness as feasibility analysis, not proof of quantum advantage.

### Step 6 — Exact Validation Dashboard

Show exact minimum energy, feasibility, best bitstring, decoded dot-bracket structure, QUBO-to-Ising summary, and energy audit summary.

### Step 7 — Graph-Aware QRAO

Explain that graph-aware QRAO uses the QUBO interaction graph to avoid packing interacting variables into the same compressed qubit.

### Step 8 — Publication Package

Show manuscript draft, results tables, and publication figures.

## 4. Safe Closing

The current contribution is an integrated and auditable research framework. The project does not claim quantum advantage or final biological validation yet.
