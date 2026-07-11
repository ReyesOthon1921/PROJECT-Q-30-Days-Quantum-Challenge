# QUBO Formulation Comparison

## Purpose

This document organizes how the current QUBO formulation should be compared against existing RNA folding and RNA-QUBO formulations.

The professor's key question is:

**Does your QUBO formulation differ from existing RNA folding formulations?**

The answer must be evidence-based. We should not claim formulation novelty until related papers are reviewed carefully.

## Current Project Formulation

The current project uses a prototype stem-based QUBO model.

- RNA sequence is cleaned into valid A/U/G/C bases.
- Candidate base pairs are generated from Watson-Crick and wobble pair rules.
- Candidate stems are built from compatible pairs.
- Each candidate stem becomes a binary decision variable.
- Linear QUBO terms reward stronger candidate stems.
- Quadratic QUBO terms penalize incompatible stems.
- The benchmark records variables, linear terms, quadratic terms, and QUBO density.

## Comparison Table

| comparison_item | traditional_rna_folding | existing_rna_qubo_to_compare | current_project | evidence_needed |
| --- | --- | --- | --- | --- |
| Decision variable | Base-pair or structural decisions. | May use base-pair variables, stem variables, or other binary encodings. | Candidate stems are represented as binary variables. | Compare variable definitions across RNA-QUBO papers. |
| Objective function | Minimizes free energy or maximizes structural score. | Uses QUBO weights based on base-pair or stem scoring. | Uses simplified stem score as a linear reward. | Compare scoring with prior thermodynamic models. |
| Penalty constraints | Constraints handled through recursion or energy rules. | Uses penalties for overlap, conflict, crossing, or invalid structures. | Adds quadratic penalties for overlapping or crossing candidate stems. | Compare exact penalty types and penalty strengths. |
| Qubit compression | Not applicable. | May not include QRAC/QRAO compression. | Adds direct vs 2-to-1 and 3-to-1 compression estimates. | Verify whether RNA-QUBO papers include compression. |

## Careful Novelty Position

This project contributes a stem-based RNA-QUBO prototype within a larger integrated benchmark framework. The exact novelty of the QUBO formulation must be verified by comparing variable definitions, constraints, penalty terms, scaling behavior, and solver pathways against existing RNA-QUBO and RNA quantum annealing literature.
