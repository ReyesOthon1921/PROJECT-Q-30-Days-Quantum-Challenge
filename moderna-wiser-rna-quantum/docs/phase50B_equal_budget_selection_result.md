# Phase 50B.1 Equal-Budget Selection Audit

- Run ID: `phase50B1_equal_budget_001`
- Development sequences only: True
- Equal SA seeds per variant: 12 (unless overridden for smoke verification)
- Equal SA steps per seed: 6000 (unless overridden for smoke verification)
- Selected variant: `short2_penalty_3`
- Formal lock recommended: True
- Phase 50 final-test used: False

## Methodological fixes

- Baseline and both candidate objectives use the same solver budget.
- Exact-optimum degeneracy is captured and scored instead of silently using only the first minimum-energy assignment.
- Resume requires a matching SHA-256 run signature.
- Per-sequence paired deltas are written against the frozen baseline.

## Equal-budget comparison

| Rank | Variant | Mixed mean F1 | dev_mixed_18 F1 | Micro F1 | Exact failure rate | SA hit rate | Mean variables |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | `short2_penalty_3` | 0.369123 | 0.857143 | 0.366013 | 0.333333 | 0.425 | 37.4 |
| 2 | `min_stem_length_3` | 0.353498 | 0.857143 | 0.364865 | 0.75 | 0.716667 | 13.1 |
| 3 | `baseline_sum` | 0.197248 | 0.0 | 0.300654 | 0.333333 | 0.433333 | 37.4 |

## Baseline comparison

- Baseline mixed mean F1: 0.197248
- Selected mixed mean F1: 0.369123
- Baseline micro F1: 0.300654
- Selected micro F1: 0.366013
- Baseline exact strict-failure rate: 0.333333
- Selected exact strict-failure rate: 0.333333

## Lock guardrails

- all_runs_successful: True
- controls_preserved: True
- mixed_f1_not_worse_than_baseline: True
- dev_mixed_18_not_worse_than_baseline: True
- micro_f1_within_noninferiority_margin: True
- exact_failure_rate_not_worse_than_baseline: True
- exact_optimal_capture_complete: True

## Frozen-data rule

The Phase 50 `final_test` split remains unused. Run it only after this audit recommends a lock and the selected configuration is committed and tagged.

## Interpretation boundary

This is a small synthetic development audit against ViennaRNA MFE references. It does not establish biological validation or quantum advantage.

## Reproducibility files

- `dataset_snapshot.csv`
- `effective_audit_config.yaml`
- `effective_strict_config.yaml`
- `equal_budget_summary.csv`
- `paired_sequence_deltas.csv`
- `selection_decision.json`
- `provisional_selected_objective_config.yaml`
- `locked_objective_config.yaml` when all guardrails pass
- per-variant `sequence_summary.csv`, `sa_runs.csv`, and `run_signature.json`
