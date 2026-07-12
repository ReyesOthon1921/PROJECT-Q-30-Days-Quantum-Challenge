# Phase 50B — Controlled QUBO Objective Ablation

## Purpose

Phase 50A showed that the exact QUBO optimum can disagree with the ViennaRNA
reference even when the solver is correct. Phase 50B therefore changes one
linear stem-scoring assumption at a time while keeping the Phase 49 overlap and
crossing penalties frozen.

## Development-only rule

This runner reads only rows whose split is `development`. The Phase 50
`final_test` rows are intentionally unavailable to the ablation command. They
must remain frozen until one objective configuration is reviewed and locked.

## Variants

The initial ablation grid includes:

- frozen sum-of-pair-rewards baseline;
- +1, +2, and +3 penalties for two-pair stems;
- minimum stem length of three;
- mean pair reward normalization;
- square-root length normalization.

Each variant is screened with a smaller multi-seed simulated-annealing budget.
The top variants are then confirmed with the full Phase 50A seed list and step
budget. Exact enumeration is used when the QUBO has no more than 20 variables.

## Selection priorities

Configurations are ranked by:

1. successful-run rate;
2. preservation of unstructured and designed-hairpin controls;
3. mean mixed-composition F1;
4. exact-solvable `dev_mixed_18` F1;
5. micro F1;
6. lower false-positive and false-negative counts;
7. solver stability;
8. lower QUBO size and runtime.

## Outputs

Each run saves:

- dataset and configuration snapshots;
- per-variant sequence and SA results;
- screen and confirmation rankings;
- selected objective metadata;
- a locked development-selected objective YAML;
- a human-readable ablation report.

## Claim boundary

These experiments compare a synthetic development set against ViennaRNA MFE
references. They do not establish biological validation or quantum advantage.
