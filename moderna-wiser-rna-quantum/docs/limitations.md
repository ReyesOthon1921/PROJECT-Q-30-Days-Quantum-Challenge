# Limitations

## 1. Prototype Dataset

The current dataset is small and controlled. It includes demonstration and synthetic RNA sequences for early benchmark development.

Future work must include larger and more biologically meaningful RNA datasets.

## 2. Reference Structure Limitation

The current benchmark uses an internal Nussinov-style reference-pair proxy. This is useful for early testing but does not replace established RNA folding tools.

Future work should compare against:

- ViennaRNA
- RNAfold
- experimentally supported RNA structures
- curated RNA secondary-structure datasets

## 3. Simplified Energy Model

The current QUBO energy model uses simplified stem scores and incompatibility penalties.

Future work should improve the energy model using more realistic RNA thermodynamic parameters.

## 4. QUBO Formulation Still Needs Literature Comparison

The stem-based QUBO formulation must be compared carefully against existing RNA-QUBO and quantum annealing RNA papers.

The paper should not claim novelty in QUBO formulation until the literature comparison is completed.

## 5. Quantum Results Are Simulator/Proxy Results

The current quantum layer includes QAOA/VQE readiness, depth estimates, energy proxies, and circuit-style benchmarking.

This does not prove real quantum advantage.

Future work should include:

- Real Qiskit circuit execution for small instances
- Noise models
- Hardware backend analysis
- Real IBM Quantum experiments when feasible

## 6. Qubit Compression Is Not Yet Validated

The qubit-compression layer estimates qubit reduction using QRAC/QRAO-style mappings.

However, reducing qubits does not automatically mean the solution quality is preserved.

Future work must test whether compressed representations maintain:

- Energy quality
- Pair prediction quality
- F1-score
- Approximation ratio
- Recoverability of useful bitstrings

## 7. Statistical Power Is Limited

Because the current benchmark dataset is small, statistical conclusions are limited.

The paper should describe the current work as a feasibility and prototype benchmark study.

## 8. No Clinical or Production Claim

This project is not a clinical RNA prediction tool.

It is not a production mRNA design system.

It is not claiming biological validation for therapeutic use.

## 9. No Quantum Advantage Claim

The project should clearly state:

**This work does not claim quantum advantage.**

The contribution is the integrated framework and benchmark pipeline.

## 10. Future Work

Future work includes:

- Larger datasets
- Stronger RNAfold/ViennaRNA validation
- Better thermodynamic modeling
- Additional classical solvers
- Real QAOA/VQE circuit experiments
- Noise simulation
- Hardware testing
- Stronger QRAC/QRAO validation
- Formal journal manuscript preparation
