# Final Limitations and Safe Claims

## Safe claim boundary

This project does not claim:

- quantum advantage
- clinical accuracy
- final biological validation
- superiority over ViennaRNA
- therapeutic readiness
- that QUBO objective values are physically equivalent to ViennaRNA MFE energies

## ViennaRNA dependency

The project includes a ViennaRNA reference layer and preflight check. Reference comparison is available when either the RNAfold command-line tool or the ViennaRNA Python binding is available in the local environment. If neither is available, the pipeline does not crash; it records a clear unavailable status.

## Energy interpretation

ViennaRNA MFE energy and the QUBO objective value are different scoring systems. The energy comparison layer is diagnostic only. It should be used to reason about relative optimization behavior, not physical thermodynamic equivalence.

## Model simplification

The current QUBO model is a simplified stem-based formulation. It does not include the full thermodynamic detail used by mature RNA folding packages. It is designed for educational/research benchmarking and quantum-readiness analysis.

## Pseudoknots

The initial model excludes pseudoknots unless explicitly handled in a future extension. This is consistent with many introductory RNA secondary-structure workflows but remains a limitation for broader biological modeling.

## Dataset limitation

The final 12-sequence benchmark is small and intended for reproducibility and demonstration. It is not large enough to support broad biological performance claims.

## Quantum limitation

The quantum layer is a readiness/prototype layer. Current results should be interpreted as simulator/resource-analysis outputs, not hardware proof of advantage.

## Compression limitation

Graph-aware compression and QRAO-style analysis are exploratory. They may reduce qubit counts in some settings but require additional quality validation after rounding or decoding.

## Appropriate final claim

The strongest appropriate claim is:

> This project provides a reproducible RNA-QUBO benchmark and validation framework that supports classical benchmarking, QUBO formulation, exact small-instance validation, solver comparison, quantum-readiness analysis, and safe future extension toward quantum optimization.
