# 1. Introduction

RNA molecules can fold into secondary structures that influence biological function. Predicting these structures is a central task in computational biology.

Traditional RNA secondary-structure prediction methods often rely on dynamic programming, thermodynamic scoring, and minimum free energy modeling. Quantum and quantum-inspired approaches require a different representation: the biological problem must be translated into an optimization model such as QUBO or Ising form.

This project explores that bridge. It builds a workflow that starts with RNA sequence preprocessing, generates candidate pairs and stems, formulates a stem-based QUBO, validates small instances exactly, and connects the resulting model to classical solvers, QAOA/VQE feasibility modules, and qubit-compression analysis.

The project is motivated by the need for careful, auditable benchmarking. Before quantum or compression results can be interpreted responsibly, the QUBO model must be traceable from sequence to variables, coefficients, assumptions, exact optima, decoded structures, and benchmark outputs.

The main research question is:

**Can RNA secondary-structure prediction be represented as a QUBO problem and evaluated through a unified classical, quantum, exact-validation, and qubit-compression benchmarking framework?**
