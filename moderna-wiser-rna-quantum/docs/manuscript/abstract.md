# Abstract

RNA secondary-structure prediction can be framed as an optimization problem, which makes it a candidate for QUBO modeling and quantum-optimization exploration.

This project presents a prototype bioinformatics-to-quantum benchmarking framework for RNA secondary-structure optimization using candidate stem generation, stem-based QUBO construction, classical solvers, QAOA/VQE feasibility modules, exact small-instance validation, QUBO-to-Ising conversion, and qubit-compression analysis.

The current validation package tracks 8 RNA sequences, includes 4 exact-validation instances, and checks 70400 total bitstring assignments by exact enumeration.

The best exact minimum QUBO energy currently observed across the exact-validation set is -13.0.

The project also adds graph-aware QRAO compression validation to test whether QUBO interaction-graph structure can guide safer variable packing.

This work does not claim quantum advantage, clinical accuracy, or final biological validation. Its contribution is an integrated, auditable research framework that connects RNA preprocessing, QUBO modeling, exact validation, quantum feasibility analysis, compression analysis, and publication-ready documentation.
