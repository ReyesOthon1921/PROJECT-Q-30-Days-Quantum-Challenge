# Phase 40 — Exact Validation Protocol

## Purpose

This protocol defines how to validate small RNA-QUBO instances exactly before interpreting quantum or compression results.

## Reason

QAOA, VQE, and QRAO results are only meaningful if the underlying QUBO can be checked against known exact solutions for small cases.

## Protocol

### Step 1 — Select Small RNA Instances

Use short controlled sequences with a small number of candidate stems.

### Step 2 — Generate Candidate Pairs

Generate candidate pairs using the selected pairing rules:

- A-U
- U-A
- G-C
- C-G
- G-U
- U-G

### Step 3 — Generate Candidate Stems

Convert candidate pairs into candidate stems.

Each stem must record all nucleotide positions and base identities.

### Step 4 — Build QUBO Coefficients

For each stem variable:

- compute linear coefficient `a_k`
- record stem score
- record biological assumption

For each pair of stems:

- compute overlap indicator `O_kl`
- compute crossing indicator `P_kl`
- compute interaction term `Gamma_kl`
- compute total quadratic coefficient `b_kl`

### Step 5 — Enumerate All Assignments

For `m` variables, enumerate all `2^m` assignments.

This is only practical for small instances.

### Step 6 — Compute Energy

For every assignment, compute:

`H(x) = sum_k a_k x_k + sum_{k<l} b_kl x_k x_l`

### Step 7 — Check Feasibility

For every assignment, check whether selected stems violate overlap or crossing constraints.

### Step 8 — Identify Exact Optimum

Record:

- exact minimum energy
- best bitstring
- degenerate minima count
- selected stems
- decoded base pairs
- dot-bracket structure
- feasibility of the optimum

### Step 9 — Compare Heuristics Later

After exact optimum is known, compare:

- greedy solver
- simulated annealing
- QAOA samples
- VQE samples
- QRAO rounded samples

using exact optimality gap.

### Step 10 — Report Limitations

Exact enumeration scales exponentially and is only for small instances.

For larger instances, exact validation should be replaced by best-known solutions, stronger classical solvers, or external benchmark references.
