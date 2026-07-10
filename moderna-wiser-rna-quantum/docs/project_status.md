\# Project Status — Classical-to-Quantum RNA Folding Dashboard



\## Current MVP Status



The project currently has a working end-to-end MVP pipeline:



RNA input

→ preprocessing

→ ViennaRNA benchmark

→ candidate pair/stem generation

→ stem-based QUBO

→ greedy solver

→ simulated annealing solver

→ evaluation metrics

→ solver comparison

→ scaling analysis



\## Completed Work



\### Classical RNA Layer



\- Dot-bracket validation

\- Base-pair extraction

\- Sequence/structure summary

\- RNA sequence cleaning

\- RNA base validation

\- GC-content calculation



\### Benchmark Layer



\- ViennaRNA Python integration

\- RNA.fold structure prediction

\- MFE energy output

\- runtime tracking



\### QUBO Preparation Layer



\- Candidate base-pair generation

\- Candidate stem generation

\- Binary variable mapping

\- estimated qubit counts



\### QUBO Layer



\- Stem-based QUBO model

\- linear rewards for stable stems

\- overlap penalties

\- crossing penalties

\- QUBO summary output



\### Solver Layer



\- Greedy stem-QUBO baseline solver

\- Simulated annealing stem-QUBO solver



\### Evaluation Layer



\- Precision

\- Recall

\- F1 score

\- true positives

\- false positives

\- false negatives

\- solver comparison against ViennaRNA



\### Scaling Layer



\- sequence length scaling

\- candidate pair scaling

\- candidate stem scaling

\- QUBO variable scaling

\- quadratic penalty scaling

\- CSV result output



\## Current Limitation



The project currently uses classical and quantum-inspired solvers. QAOA and VQE are not implemented yet.



\## Next Steps



1\. Save dashboard screenshots.

2\. Add final demo evidence.

3\. Prepare professor-ready explanation.

4\. Add optional QAOA prototype.

5\. Add optional VQE prototype.

6\. Prepare web deployment if needed.

