\# Final Project Summary



\## Project Title



Optimization of RNA/mRNA Secondary Structure Prediction Using Classical, Bioinformatics, and Quantum-Inspired Computing



\## Project Status



This project now includes a working full-stack research prototype for RNA/mRNA secondary-structure optimization.



The system connects:



RNA sequence input  

→ classical RNA validation  

→ ViennaRNA benchmark  

→ candidate pair and stem generation  

→ QUBO formulation  

→ greedy and simulated annealing solvers  

→ evaluation metrics  

→ scaling analysis  

→ bioinformatics metrics  

→ QAOA readiness  

→ VQE readiness  

→ quantum benchmark  

→ QAOA circuit simulation  

→ VQE circuit simulation  

→ QAOA vs VQE circuit comparison  

→ QAOA parameter sweep  

→ web dashboard deployment



\## Current Achievement



The project successfully demonstrates a complete research pipeline from RNA sequence preprocessing to quantum-ready optimization experiments.



The quantum side does not claim quantum advantage. Instead, it demonstrates that the RNA/mRNA folding problem can be represented as a QUBO, mapped toward an Ising/Hamiltonian form, and tested through small QAOA-style and VQE-style simulator circuits.



\## Dashboard Features



\- RNA sequence validation

\- dot-bracket structure validation

\- ViennaRNA-style benchmark layer

\- candidate base-pair generation

\- candidate stem generation

\- QUBO builder

\- greedy solver

\- simulated annealing solver

\- solver comparison

\- evaluation metrics

\- scaling analysis

\- algorithm comparison graphs

\- bioinformatics metrics

\- BLAST and RCSB research links

\- QAOA readiness prototype

\- VQE readiness prototype

\- quantum benchmark layer

\- QAOA circuit prototype

\- VQE circuit prototype

\- QAOA vs VQE circuit comparison

\- QAOA parameter sweep



\## Quantum-Side Summary



The quantum side currently includes:



1\. QUBO formulation using candidate RNA stems as binary variables.

2\. QAOA readiness using a small QUBO subset.

3\. VQE readiness using a Hamiltonian/Ising-style subset.

4\. QAOA circuit prototype using Qiskit Aer.

5\. VQE circuit prototype using Qiskit Aer.

6\. Circuit comparison between QAOA and VQE.

7\. QAOA parameter sweep over gamma and beta values.



\## Variable Compression Research Extension



The project also includes a variable-compression research layer. This layer compares the current direct one-variable-per-qubit QUBO mapping against QRAC/QRAO-style compression estimates and qubit-efficient log-style encoding estimates.



The QRAO subset mapping assigns RNA candidate stem variables into compressed qubit slots using Pauli-axis labels such as X, Y, and Z. This does not solve the compressed optimization problem yet. It is a research extension that estimates whether future RNA/QUBO instances could reduce qubit requirements before QAOA or VQE testing.



This layer helps compare:



\- direct one-variable-per-qubit mapping

\- 2-to-1 QRAC estimate

\- 3-to-1 QRAC estimate

\- 3-to-2 QRAC estimate

\- qubit-efficient log encoding estimate



\## Current Limitations



\- This is a simulator prototype, not a quantum advantage claim.

\- QAOA uses a small subset of the full QUBO.

\- VQE does not yet include a full classical optimizer loop.

\- Larger RNA sequences create scaling challenges.

\- Current circuit tests are local simulations, not hardware runs.

\- Future work should improve energy evaluation, parameter optimization, and hardware-readiness analysis.



\## Future Work



Recommended next research steps:



\- VQE parameter sweep

\- measured-bitstring energy evaluation

\- improved QUBO penalty tuning

\- higher-order constraint exploration

\- hardware-readiness analysis for IBM Quantum

\- comparison against additional RNA datasets

\- integration with more bioinformatics validation tools



\## Final Statement



This project is now a complete prototype research platform for exploring RNA/mRNA secondary-structure prediction through classical optimization, bioinformatics metrics, QUBO modeling, and quantum-inspired circuit simulation.

