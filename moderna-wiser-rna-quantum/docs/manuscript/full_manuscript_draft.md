# Full Manuscript Draft

**Working Title:** A Bioinformatics-to-Quantum Benchmarking Framework for RNA Secondary Structure Prediction Using QUBO, QAOA, VQE, and Qubit-Compression Analysis

**Status:** Draft manuscript package for professor review. This is not a final journal submission.

---

# Abstract

RNA secondary-structure prediction can be framed as an optimization problem, which makes it a candidate for QUBO modeling and quantum-optimization exploration.

This project presents a prototype bioinformatics-to-quantum benchmarking framework for RNA secondary-structure optimization using candidate stem generation, stem-based QUBO construction, classical solvers, QAOA/VQE feasibility modules, exact small-instance validation, QUBO-to-Ising conversion, and qubit-compression analysis.

The current validation package tracks 8 RNA sequences, includes 4 exact-validation instances, and checks 70400 total bitstring assignments by exact enumeration.

The best exact minimum QUBO energy currently observed across the exact-validation set is -13.0.

The project also adds graph-aware QRAO compression validation to test whether QUBO interaction-graph structure can guide safer variable packing.

This work does not claim quantum advantage, clinical accuracy, or final biological validation. Its contribution is an integrated, auditable research framework that connects RNA preprocessing, QUBO modeling, exact validation, quantum feasibility analysis, compression analysis, and publication-ready documentation.

---

# 1. Introduction

RNA molecules can fold into secondary structures that influence biological function. Predicting these structures is a central task in computational biology.

Traditional RNA secondary-structure prediction methods often rely on dynamic programming, thermodynamic scoring, and minimum free energy modeling. Quantum and quantum-inspired approaches require a different representation: the biological problem must be translated into an optimization model such as QUBO or Ising form.

This project explores that bridge. It builds a workflow that starts with RNA sequence preprocessing, generates candidate pairs and stems, formulates a stem-based QUBO, validates small instances exactly, and connects the resulting model to classical solvers, QAOA/VQE feasibility modules, and qubit-compression analysis.

The project is motivated by the need for careful, auditable benchmarking. Before quantum or compression results can be interpreted responsibly, the QUBO model must be traceable from sequence to variables, coefficients, assumptions, exact optima, decoded structures, and benchmark outputs.

The main research question is:

**Can RNA secondary-structure prediction be represented as a QUBO problem and evaluated through a unified classical, quantum, exact-validation, and qubit-compression benchmarking framework?**

---

# 2. Related Work

The project connects several research areas:

## RNA Folding

The RNA side includes secondary-structure prediction, base-pairing rules, dot-bracket notation, minimum free energy methods, Nussinov-style dynamic programming, Zuker-style approaches, McCaskill partition functions, and ViennaRNA/RNAfold-style validation.

## QUBO and Ising Formulations

The optimization side includes binary decision variables, objective functions, penalty constraints, Hamiltonian construction, QUBO matrix conventions, and QUBO-to-Ising mappings.

## Quantum Algorithms

The quantum side includes QAOA, VQE, quantum annealing, parameter sweeps, measured bitstrings, hardware-readiness estimates, and NISQ-era limitations.

## Qubit Compression

The compression side includes direct one-variable-per-qubit encoding, QRAC, QRAO, variable grouping, Pauli X/Y/Z assignment, rounding, and interaction-graph-aware packing.

The current literature review matrix contains 11 tracked entries or placeholders. These references must be expanded and verified before final journal submission.

---

# 3. Methodology

The methodology follows an end-to-end research pipeline:

`RNA sequence -> preprocessing -> candidate pairs -> candidate stems -> stem-QUBO formulation -> exact validation -> classical benchmark -> quantum feasibility -> qubit compression -> hardware readiness -> publication outputs`

## 3.1 RNA Preprocessing

Input sequences are cleaned and represented using the RNA alphabet A, U, G, and C. Sequence length, GC content, AU content, candidate-pair count, and candidate-stem count are recorded.

## 3.2 Candidate Pair and Stem Generation

Candidate base pairs are generated using Watson-Crick and wobble-pair rules. Candidate stems are then constructed from compatible stacked or grouped base-pair candidates.

## 3.3 Stem-Based QUBO Formulation

Each candidate stem is represented as a binary variable. Favorable stems receive negative linear energy, while incompatible stem selections receive quadratic penalties for overlap or forbidden crossing patterns.

## 3.4 Exact Validation

For small QUBO instances, all bitstrings are enumerated to identify exact minimum energy, degenerate minima, feasibility, decoded pairs, dot-bracket output, and energy decomposition.

## 3.5 QUBO-to-Ising Conversion

The QUBO is converted into Ising-style coefficients to support cost-Hamiltonian interpretation for QAOA and VQE-style modules.

## 3.6 Classical and Quantum Benchmarking

Classical benchmarking uses greedy and simulated annealing baselines. Quantum modules include QAOA readiness, VQE readiness, circuit prototypes, parameter sweeps, measured bitstring energy, and hardware-readiness checks.

## 3.7 Graph-Aware QRAO Compression

The QUBO interaction graph is used to guide compression. Interacting variables are not assigned to the same compressed qubit under the graph-aware QRAO packing logic.

## 3.8 External Validation Planning

RNAfold/ViennaRNA, BLAST, and RCSB PDB are planned as external validation/context layers. These outputs must be manually executed and verified before being treated as evidence.

---

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

---

# 5. Discussion

The project has moved beyond a simple dashboard into an auditable research workflow.

The most important progress is the addition of exact small-instance validation. This gives the project a ground-truth layer for small QUBO instances before interpreting heuristic, quantum, or compression outputs.

The graph-aware QRAO phase also strengthens the compression direction. Instead of only estimating qubit savings by dividing variables into smaller counts, the project now uses the QUBO interaction graph to avoid placing interacting variables on the same compressed qubit.

This is important because compression should not be treated as a simple variable-count reduction. It must be evaluated as a relaxation that requires mapping, rounding, feasibility checks, and comparison against exact or best-known solutions.

The biological validation side is still being expanded. Phase 45 added dataset tracking and external-validation planning, but RNAfold/ViennaRNA, BLAST, and RCSB results still need to be manually collected and verified before biological claims are made.

---

# 6. Limitations

This project is a prototype benchmark and feasibility framework.

The project does not claim:

- quantum advantage,
- clinical accuracy,
- production RNA design readiness,
- final biological validation,
- proven QUBO novelty before literature comparison,
- proven compression improvement before rounded-solution validation.

Exact enumeration is only practical for small QUBO instances because the number of assignments grows exponentially.

The current energy model is simplified and does not fully replace thermodynamic RNA folding models.

The QAOA and VQE layers are feasibility/proxy layers and should not be interpreted as evidence of quantum advantage.

The graph-aware QRAO layer validates mapping logic, but future work must test rounded compressed solutions against exact optima and biological reference structures.

The RNAfold, BLAST, and RCSB validation plans are not complete until the external outputs are collected and recorded.

---

# 7. Conclusion

This project demonstrates an end-to-end RNA secondary-structure optimization research workflow that connects bioinformatics preprocessing, stem-based QUBO formulation, exact validation, classical benchmarking, QAOA/VQE feasibility analysis, QUBO-to-Ising conversion, graph-aware QRAO compression, hardware-readiness evaluation, and publication-ready documentation.

The strongest current contribution is not a claim of quantum advantage. The strongest contribution is the integrated and auditable framework.

The project now provides a structured way to trace RNA sequence inputs into QUBO variables, coefficients, exact optima, energy audits, quantum-feasibility outputs, compression mappings, and manuscript-ready results.

---

# 8. Future Work

Future work should focus on:

1. Expanding the RNA dataset with verified biological references.
2. Running and recording RNAfold/ViennaRNA outputs.
3. Adding reference dot-bracket structures and MFE values.
4. Comparing QUBO predictions against RNAfold base-pair sets.
5. Testing rounded QRAO compressed solutions against exact optima.
6. Adding noise simulation and hardware-aware circuit constraints.
7. Expanding the literature review with verified citations.
8. Preparing the manuscript for professor review and possible journal formatting.

The next project phase should focus on final demo packaging, README cleanup, deployment verification, and professor-review readiness.

---
