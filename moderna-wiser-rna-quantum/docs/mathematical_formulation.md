# Phase 40 — Mathematical Formulation

## Purpose

This document defines the mathematical layer for the RNA Stem-QUBO prototype.

The goal is to make the model explicit, auditable, and reproducible before making stronger claims about QAOA, VQE, hardware readiness, or qubit compression.

## Current Research Position

This project is a prototype benchmark and feasibility framework. It does not claim quantum advantage, clinical accuracy, final biological validation, or a novel QUBO formulation before literature comparison.

## Traceability Principle

Every predicted base pair should be traceable back to:

1. an RNA sequence,
2. a candidate structural element,
3. a binary variable,
4. a QUBO coefficient,
5. a biological or mathematical assumption,
6. a decoded structure,
7. a reproducible experiment.

The intended chain is:

`RNA sequence -> candidate pairs -> candidate stems -> binary variables -> QUBO coefficients -> exact validation -> decoded RNA structure`

## RNA Sequence

Let an RNA sequence be:

`R = (r_1, r_2, ..., r_n)`

where each base satisfies:

`r_i in {A, C, G, U}`

The implementation cleans input sequences by converting thymine to uracil and removing invalid characters.

## Candidate Base Pairs

The candidate pair set is:

`E = {(i, j): 0 <= i < j < n, j - i >= h_min, r_i ~ r_j}`

where `r_i ~ r_j` means the pair is biologically allowed under the selected pairing rules.

Current allowed pair rules:

- A-U
- U-A
- G-C
- C-G
- G-U
- U-G

The `G-U` and `U-G` rules represent wobble pairs.

## Candidate Stem Set

The main project formulation uses candidate stems as variables.

A candidate stem is a stack or grouped set of candidate base pairs:

`s_k = { (i, j), (i+1, j-1), ..., (i+l_k-1, j-l_k+1) }`

where `l_k` is the stem length.

## Binary Variables

For every candidate stem `s_k`, define one binary decision variable:

`x_k = 1` if stem `s_k` is selected.

`x_k = 0` if stem `s_k` is not selected.

## Stem-Based QUBO Objective

The general stem-QUBO form is:

`H_stem(x) = sum_k a_k x_k + sum_{k<l} b_kl x_k x_l`

where:

- `a_k` is the linear coefficient for candidate stem `s_k`.
- `b_kl` is the quadratic coefficient between candidate stems `s_k` and `s_l`.

## Current Linear Coefficient

The current prototype uses a simplified stem score:

- G-C or C-G pair contributes 3 points.
- A-U or U-A pair contributes 2 points.
- G-U or U-G wobble pair contributes 1 point.

Because the QUBO is minimized, favorable stems receive negative linear energy:

`a_k = -stem_score(s_k) + fragment_penalty + local_context_penalty`

The current minimal prototype keeps fragment and local context terms simple and explicit.

## Current Quadratic Coefficients

The current prototype separates quadratic coefficients into interpretable parts:

`b_kl = M_overlap * O_kl + M_crossing * P_kl + Gamma_kl`

where:

- `O_kl = 1` when stems overlap by sharing at least one nucleotide.
- `P_kl = 1` when stems create a forbidden crossing pattern.
- `Gamma_kl` is a compatible interaction term.

The minimal defensible prototype uses:

`Gamma_kl = 0`

This keeps the first model auditable before adding more biological interaction terms.

## Overlap Rule

Two stems overlap if they use at least one common nucleotide.

Overlap is currently treated as a hard structural conflict because one nucleotide should not be paired in two selected stems at the same time.

## Crossing / Pseudoknot Rule

Two pairs `(i, j)` and `(k, l)` create a crossing pattern when:

`i < k < j < l`

or:

`k < i < l < j`

The current prototype treats crossing as forbidden unless a future model explicitly includes pseudoknot classes.

Important: if pseudoknots are included later, crossing should not simply be treated as a hard penalty. The allowed pseudoknot class and its energy model must be defined.

## QUBO Matrix Convention

The QUBO is represented as:

`H(x) = x^T Q x`

The project records linear coefficients and upper-triangular quadratic coefficients separately to avoid factor-of-two confusion.

Current storage convention:

- diagonal / linear terms are stored as `a_k`.
- upper-triangular off-diagonal terms are stored as `b_kl`.

## QUBO-to-Ising Mapping

For QAOA/VQE cost Hamiltonian construction, binary variables can be mapped to spin variables:

`x_i = (1 - z_i) / 2`

where:

`z_i in {-1, +1}`

The Ising form is:

`H_I(z) = C + sum_i h_i z_i + sum_{i<j} J_ij z_i z_j`

with:

`J_ij = b_ij / 4`

`h_i = -a_i / 2 - (1/4) * sum_{j != i} b_ij`

`C = (1/2) * sum_i a_i + (1/4) * sum_{i<j} b_ij`

The constant offset `C` does not change the minimizing bitstring, but it matters when numerical quantum energies are compared with QUBO energies.

## Validation Requirement

For small candidate sets, the project must enumerate all assignments:

`x in {0, 1}^m`

and report:

- exact global minimum,
- degenerate minima,
- best bitstring,
- decoded stems,
- decoded base pairs,
- dot-bracket output,
- feasibility status,
- exact optimality gap for heuristic solvers,
- term-by-term energy audit.

## QRAO Compression Update

QRAO compression must be treated as a relaxation, not an exact equivalence.

The QUBO interaction graph is:

`G_Q = (V, E_Q)`

where each vertex is a binary variable and each edge represents a nonzero quadratic coefficient.

Important encoding rule:

Variables connected by an edge in the QUBO interaction graph should not be packed into the same qubit under standard QRAC/QRAO construction.

This means the compression layer should become graph-aware and should use coloring or packing rules before assigning variables to Pauli X/Y/Z slots.

## Safe Research Claim

The current safe claim is:

This project contributes an integrated bioinformatics-to-quantum benchmark framework and is adding a mathematical traceability layer to make the RNA Stem-QUBO model explicit, auditable, and reproducible.
