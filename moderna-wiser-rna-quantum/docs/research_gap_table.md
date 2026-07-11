# Research Gap Table

## Main Research Gap

The main research gap is the lack of a unified, reproducible benchmark workflow that connects RNA sequence preprocessing, QUBO formulation, classical optimization, QAOA/VQE feasibility, qubit compression, hardware readiness, and publication-ready benchmark tables.

The project should not claim quantum advantage.

The strongest contribution is the integrated benchmark framework.

## Gap Table

| paper_area | what_existing_work_does | what_is_missing | our_project_response |
| --- | --- | --- | --- |
| RNA folding tools | Predicts RNA secondary structure using classical folding methods. | Usually not connected to QUBO, QAOA, VQE, qubit compression, and hardware-readiness in one workflow. | Adds a path from RNA preprocessing into QUBO and quantum-ready benchmark evaluation. |
| QUBO RNA folding | Maps RNA folding into binary optimization using variables and penalties. | Often limited to formulation or solver results. | Adds benchmark tables, classical solvers, quantum feasibility, compression, and hardware-readiness metrics. |
| Quantum algorithms | Uses QAOA, VQE, or quantum annealing for optimization. | Often does not evaluate RNA-QUBO practicality with sequence length, variables, depth, and hardware readiness together. | Adds QAOA/VQE readiness, circuit-depth estimates, energy proxies, bitstrings, and hardware-readiness labels. |
| Qubit compression | Studies QRAC/QRAO-style compression for optimization. | RNA-QUBO-specific compression quality is not yet established. | Adds direct vs compressed qubit estimates and QRAO-style mapping as a research extension. |

## Draft Research Gap Statement

Existing RNA secondary-structure prediction tools are strong classical methods, and existing QUBO or quantum optimization studies explore important pieces of the problem. However, many approaches focus on a single layer: RNA folding, QUBO formulation, quantum solver testing, or hardware feasibility.

This project addresses that gap by creating an integrated bioinformatics-to-quantum benchmark workflow.
