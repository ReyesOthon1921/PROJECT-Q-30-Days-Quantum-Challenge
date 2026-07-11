# Novelty Questions

This document organizes the key research questions from the professor into paper-ready form.

## Question 1

### Does the QUBO formulation differ from existing RNA folding formulations?

Current answer:

The project uses a stem-based QUBO formulation where candidate stems are represented as binary decision variables. Linear terms reward favorable stems, while quadratic penalty terms discourage incompatible stems such as overlapping or crossing structures.

This must be compared against existing RNA-QUBO and RNA quantum annealing formulations in the literature.

Evidence needed:

- Literature table comparing variable definitions
- Literature table comparing constraints
- Comparison of pair-based vs stem-based modeling
- Comparison of QUBO term growth
- Discussion of pseudoknot or incompatibility handling

## Question 2

### Does the variable-compression strategy reduce qubit requirements while maintaining solution quality?

Current answer:

The project currently estimates qubit reduction using direct encoding, 2-to-1 QRAC-style compression, 3-to-1 QRAC/QRAO-style compression, and log-style qubit estimates.

The project can show qubit-count reduction estimates, but it must still validate whether compressed mappings preserve solution quality.

Evidence needed:

- Direct qubit count
- Compressed qubit count
- Reduction percentage
- Energy comparison
- F1-score comparison
- Mapping error or approximation-quality discussion

Important wording:

Compression is currently a research direction and benchmark extension, not proof of improved RNA folding performance.

## Question 3

### Does the benchmarking include datasets or evaluation metrics not previously reported together?

Current answer:

The project combines biological metrics, optimization metrics, quantum metrics, and compression metrics into one final benchmark table.

Metrics include:

- Sequence length
- GC content
- Candidate pairs
- Candidate stems
- QUBO variables
- Linear and quadratic terms
- QUBO density
- Runtime
- Energy
- Sensitivity
- Specificity
- Precision
- Recall
- F1-score
- Estimated qubits
- Circuit-depth estimates
- Bitstring proxy
- Qubit reduction percentage
- Hardware-readiness label

Evidence needed:

- Final publication benchmark table
- Comparison to what previous papers report
- Clear statement of which metrics are combined in this project

## Question 4

### Does the framework reveal new insights into when QAOA or VQE becomes practical for RNA optimization?

Current answer:

The framework estimates QAOA and VQE practicality by tracking QUBO variable count, estimated qubits, circuit-depth estimates, runtime, energy proxy values, bitstring output, and hardware-readiness labels.

The current results are simulator and proxy-based. The next step is to test small cases with actual Qiskit circuits and compare runtime, depth, and measured bitstring quality.

Evidence needed:

- QAOA circuit depth by variable count
- VQE circuit depth by variable count
- Hardware-readiness table
- Qubit-count threshold discussion
- NISQ limitation discussion
- Noise simulation in future work

## Proposed Novelty Statement

This project contributes an end-to-end bioinformatics-to-quantum benchmarking framework for RNA secondary-structure optimization. The framework connects RNA preprocessing, stem-based QUBO formulation, classical solver benchmarking, QAOA/VQE feasibility analysis, qubit-compression estimates, and hardware-readiness evaluation into one reproducible workflow.

The novelty is the integrated benchmark framework, not a claim of quantum advantage.
