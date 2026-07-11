# Research Problem

## Main Research Problem

RNA secondary-structure prediction is a biological optimization problem. The structure of an RNA molecule depends on which bases pair with each other and how those pairings form stems, loops, and other secondary-structure features.

Traditional RNA folding tools usually focus on thermodynamic modeling and minimum free energy prediction. Quantum and quantum-inspired methods require a different representation: the problem must be translated into a binary optimization model such as QUBO or Ising form.

The research problem for this project is:

**Can RNA secondary-structure prediction be represented as a QUBO problem and evaluated through a unified classical, quantum, and qubit-compression benchmarking framework?**

## Why This Problem Matters

RNA structure prediction is important because RNA structure affects biological function. For mRNA design, RNA therapeutics, and computational biology, predicting stable and meaningful RNA secondary structures is a valuable research direction.

Quantum computing introduces a possible future path for optimization, but current quantum hardware is limited by:

- Qubit count
- Circuit depth
- Noise
- Connectivity
- Gate errors
- Measurement uncertainty

Because of these limitations, the project does not claim quantum advantage. Instead, it asks a more careful research question:

**What can be learned by building a transparent benchmark that compares RNA-QUBO problems across classical solvers, quantum algorithm prototypes, and qubit-compression estimates?**

## Core Research Questions

1. Does the stem-based QUBO formulation differ from existing RNA folding QUBO formulations?
2. Can QRAC/QRAO-style qubit compression reduce qubit requirements while maintaining solution quality?
3. Can biological metrics, optimization metrics, quantum metrics, and compression metrics be reported together in one benchmark?
4. Can the framework reveal when QAOA or VQE becomes practical for RNA optimization?
5. What are the current limitations of using NISQ-era quantum methods for RNA-QUBO problems?

## Research Position

This project should be described as a prototype benchmark and feasibility study.

It is not a final biological prediction model.

It is not a clinical tool.

It does not prove quantum advantage.

The contribution is the integrated workflow:

**RNA sequence → bioinformatics preprocessing → QUBO formulation → classical benchmark → quantum benchmark → qubit compression → hardware readiness → publication results.**
