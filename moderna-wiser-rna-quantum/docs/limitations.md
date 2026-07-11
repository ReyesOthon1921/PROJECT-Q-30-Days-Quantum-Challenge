# Limitations

## 1. Prototype Status

This project is a prototype benchmark and feasibility framework.

## 2. No Quantum Advantage Claim

The project does not claim quantum advantage.

## 3. No Clinical or Production Claim

The project is not a clinical RNA prediction tool and is not production-ready for mRNA design.

## 4. QUBO Novelty Not Yet Proven

The stem-based QUBO formulation must be compared carefully against existing RNA-QUBO literature before claiming novelty.

## 5. Simplified Energy Model

The current scoring model uses simplified stem rewards and penalties. Future work should include stronger thermodynamic modeling.

## 6. Exact Validation Limited to Small Instances

Exact enumeration scales exponentially and can only be used for small QUBO instances.

## 7. Quantum Results Are Simulator/Proxy Results

Current QAOA/VQE outputs are feasibility and simulator/proxy results.

## 8. Compression Not Yet Validated

QRAC/QRAO-style compression may reduce qubit requirements, but solution quality, feasibility, and rounding behavior must be validated.

## 9. External Biological Validation Still Needed

The project still needs stronger comparison against ViennaRNA/RNAfold, curated RNA structures, and larger datasets.

## 10. Current Focus

The current focus is making the QUBO layer explicit, traceable, and auditable before making stronger quantum or compression claims.
