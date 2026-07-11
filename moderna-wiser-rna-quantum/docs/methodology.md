# Methodology

## Overview

The methodology follows an end-to-end RNA-QUBO research workflow:

`RNA sequence -> preprocessing -> candidate pairs -> candidate stems -> QUBO formulation -> exact validation -> classical benchmark -> quantum feasibility -> qubit compression -> hardware readiness -> publication results`

## 1. RNA Sequence Input

The input is an RNA sequence over A, U, G, and C. Any thymine is converted to uracil during preprocessing.

## 2. Bioinformatics Preprocessing

The pipeline computes length, GC content, valid bases, candidate base pairs, candidate stems, and structure-related features.

## 3. Candidate Pair Generation

Candidate pairs are generated using Watson-Crick and wobble pairing rules.

## 4. Candidate Stem Generation

Candidate stems are generated from compatible base pairs. Each stem becomes a possible structural element.

## 5. Stem-Based QUBO Formulation

Each candidate stem becomes a binary decision variable. Linear terms reward favorable stems. Quadratic terms penalize incompatible stems such as overlaps and forbidden crossing patterns.

## 6. Mathematical Traceability

Every predicted base pair should trace back to a stem, every stem to a variable, every variable to a coefficient, and every coefficient to a modeling assumption.

## 7. Exact Small-Instance Validation

For small QUBO instances, every bitstring is enumerated to find the exact global minimum, degenerate minima, feasibility, decoded pairs, and dot-bracket structure.

## 8. Energy Audit

The project exports term-by-term energy contributions for the exact optimum. This separates linear rewards, overlap penalties, crossing penalties, and total QUBO energy.

## 9. Classical Benchmark

Greedy and simulated annealing solvers are used as classical baselines. Their results should later be compared against exact optima for small instances.

## 10. Quantum Benchmark

QAOA and VQE layers are treated as feasibility and simulator/proxy experiments. They do not prove quantum advantage.

## 11. Qubit Compression

Direct encoding is compared with QRAC/QRAO-style compression estimates. After Christian's feedback, this layer should become graph-aware by using the QUBO interaction graph.

## 12. Hardware Readiness

Hardware-readiness analysis evaluates qubit count, circuit depth, connectivity, shots, and NISQ limitations.

## 13. Publication Output

The project generates benchmark tables, figures, documentation, literature review notes, QUBO comparison notes, exact validation results, and traceability outputs.
