\# Demo Script — Classical-to-Quantum RNA Folding Dashboard



\## Project Goal



This project builds a full-stack Classical-to-Quantum RNA Folding Dashboard for RNA/mRNA secondary-structure prediction research.



The pipeline connects:



RNA sequence input

→ RNA preprocessing

→ dot-bracket validation

→ ViennaRNA classical benchmark

→ candidate base-pair generation

→ candidate stem generation

→ stem-based QUBO builder

→ greedy QUBO baseline solver

→ evaluation against ViennaRNA

→ scaling analysis



\## Current Completed Phases



\### Phase 1 — Classical RNA Foundation



Completed:

\- dot-bracket validation

\- base-pair extraction

\- dot-bracket summary

\- sequence/structure length validation



\### Phase 2 / Phase 0 Integration — Flask Dashboard



Completed:

\- Flask backend

\- browser dashboard

\- API routes for RNA structure validation

\- frontend buttons connected to Python modules



\### Phase 3 — RNA Sequence Preprocessing



Completed:

\- RNA sequence cleaning

\- A/U/G/C validation

\- GC-content calculation

\- candidate base-pair counting



\### Phase 4 — ViennaRNA Benchmark



Completed:

\- ViennaRNA Python integration

\- RNA.fold benchmark

\- MFE structure

\- MFE energy

\- runtime measurement



\### Phase 5 — QUBO Candidate Generation



Completed:

\- candidate base-pair variables

\- candidate stem variables

\- variable index maps

\- estimated qubit counts



\### Phase 6 — Stem-Based QUBO Builder



Completed:

\- linear rewards for favorable stems

\- penalties for overlapping stems

\- penalties for crossing stems

\- QUBO variable and penalty summary



\### Phase 7 — Greedy Solver Layer



Completed:

\- greedy stem-QUBO baseline solver

\- predicted dot-bracket structure

\- selected stems

\- selected base pairs

\- objective score



\### Phase 8 — Evaluation Metrics



Completed:

\- comparison against ViennaRNA

\- precision

\- recall

\- F1 score

\- true positives

\- false positives

\- false negatives



\### Phase 9 — Scaling Analysis



Completed:

\- sequence length scaling

\- candidate pair scaling

\- candidate stem scaling

\- QUBO variable scaling

\- quadratic penalty scaling

\- runtime tracking

\- CSV output



\## Demo Button Order



1\. Analyze Sequence

2\. Run Classical Benchmark

3\. Generate Candidate Pairs

4\. Generate Candidate Stems

5\. Build Stem QUBO

6\. Run Greedy Solver

7\. Evaluate Greedy vs ViennaRNA

8\. Run Scaling Analysis

9\. Validate Structure



\## Current Research Note



The greedy QUBO solver is a baseline, not the final quantum solver.  

The next research step is to add stronger solver layers such as simulated annealing, QAOA, and eventually VQE for comparison.

