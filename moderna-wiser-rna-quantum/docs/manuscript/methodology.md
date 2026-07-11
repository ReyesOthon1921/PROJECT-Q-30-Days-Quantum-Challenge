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
