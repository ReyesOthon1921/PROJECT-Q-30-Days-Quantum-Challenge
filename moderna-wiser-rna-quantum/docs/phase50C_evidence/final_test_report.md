# Phase 50C Frozen Final-Test Report

- Run ID: `phase50C_final_test_001`
- Final-test sequences: 8
- Solver budget equal across variants: True
- Locked variant: `short2_penalty_3`
- Objective selection or retuning performed: False
- Final-test split consumed: True

## Final-test comparison

| Variant | Mixed mean F1 | Micro F1 | Precision | Recall | Exact match | FP | FN | SA hit rate | Mean variables |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `baseline_sum` | 0.284703 | 0.335878 | 0.305556 | 0.372881 | 0.25 | 50 | 37 | 0.46875 | 49.25 |
| `short2_penalty_3` | 0.630757 | 0.650794 | 0.61194 | 0.694915 | 0.375 | 26 | 18 | 0.427083 | 49.25 |

## Locked-minus-baseline deltas

- Mixed mean F1 delta: 0.346054
- Micro F1 delta: 0.314916
- False-positive delta: -24.0
- False-negative delta: -19.0
- Exact-match-rate delta: 0.125
- SA best-energy-hit-rate delta: -0.041667

## Frozen-protocol confirmation

- Phase 50B lock decision verified before execution.
- Git lock tag verified before execution.
- Only the eight frozen `final_test` rows were loaded.
- Baseline and locked objective used the same 12 seeds and 6,000 SA steps.
- No parameter selection, ranking, or objective changes were performed.
- Receipt SHA-256: `c2f73d46285066c7e0480544fb12b7c9ff187bd1327a9eafa84fecddc72b075c`

## Interpretation boundary

This is a small synthetic benchmark against ViennaRNA MFE references. It does not establish biological validation, clinical usefulness, physical equivalence between ViennaRNA energies and QUBO scores, or quantum advantage.

## Reproducibility files

- `dataset_snapshot.csv`
- `effective_final_test_config.yaml`
- `effective_locked_objective_config.yaml`
- `lock_decision_snapshot.json`
- `final_test_summary.csv`
- `paired_final_test_deltas.csv`
- `final_test_receipt.json`
- per-variant `sequence_summary.csv`, `sa_runs.csv`, and `run_signature.json`
