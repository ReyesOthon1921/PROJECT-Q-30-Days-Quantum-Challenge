# Novelty Questions

## Current Safe Position

The project should not claim quantum advantage or a novel QUBO formulation before validation and literature comparison are complete.

The strongest current contribution is the integrated bioinformatics-to-quantum benchmark workflow.

## Question 1 — Does the QUBO formulation differ from existing RNA folding formulations?

Current answer:

The project uses a stem-based QUBO prototype. The exact novelty of the formulation must be verified against existing RNA-QUBO and RNA quantum annealing literature.

Evidence needed:

- variable definitions,
- objective terms,
- penalty terms,
- QUBO matrix convention,
- pseudoknot/crossing treatment,
- scaling behavior,
- solver pathway comparison.

## Question 2 — Does the model have mathematical traceability?

Current answer:

Phase 40 adds traceability tables, exact validation, and energy auditing so every predicted structure can be traced back to variables, coefficients, and assumptions.

## Question 3 — Does variable compression reduce qubits while preserving quality?

Current answer:

The project currently estimates qubit reduction. The next step is to test whether compression preserves feasibility and objective quality after rounding.

## Question 4 — Does the benchmark combine metrics not usually reported together?

Current answer:

Yes, the framework is designed to combine biological, optimization, quantum, compression, and hardware-readiness metrics. This combined structure is the safest current novelty claim.

## Question 5 — Does the framework reveal when QAOA or VQE becomes practical?

Current answer:

The framework can study this through QUBO variable count, circuit depth, bitstring quality, exact optimality gap, and hardware-readiness metrics.
