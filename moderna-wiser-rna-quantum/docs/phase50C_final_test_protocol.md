# Phase 50C — One-Time Frozen Final-Test Evaluation

Phase 50C evaluates the locked Phase 50B objective exactly once on the frozen
`final_test` split. It compares the frozen Phase 50A baseline against the locked
`short2_penalty_3` objective under the same solver budget.

## Required lock state

- `configs/phase50B_lock_decision.json` must report `lock_recommended: true`.
- The selected variant must be `short2_penalty_3`.
- `configs/phase50B_locked_objective_config.yaml` must contain the exact locked
  objective values.
- Git tag `phase50B-objective-locked` must exist locally.
- The current branch must be `phase50C-final-test`.

## One-time consumption rule

The evaluator creates `results/phase50C_final_test/final_test_registry.json` at
run start. A matching interrupted run may resume with the same run ID and run
signature. After completion, additional final-test runs are refused.

The evaluator has no split option and no solver-budget overrides. The only
execution path evaluates the eight frozen `final_test` sequences.

## Outputs

- `dataset_snapshot.csv`
- `effective_final_test_config.yaml`
- `effective_locked_objective_config.yaml`
- `lock_decision_snapshot.json`
- `final_test_summary.csv`
- `paired_final_test_deltas.csv`
- `final_test_report.md`
- `final_test_receipt.json`
- per-variant `sequence_summary.csv`, `sa_runs.csv`, and `run_signature.json`

## Interpretation boundary

This is a small synthetic benchmark against ViennaRNA MFE references. It does
not establish biological validation, clinical usefulness, physical equivalence
between ViennaRNA energies and QUBO scores, or quantum advantage.
