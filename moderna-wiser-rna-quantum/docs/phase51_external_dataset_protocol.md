# Phase 51A — External Dataset Declaration and Leakage Audit

## Research question

Does the frozen `short2_penalty_3` objective maintain its improvement over the
frozen baseline on a newly declared, independent RNA dataset with broader
sequence, length, and structural diversity?

## Phase boundary

Phase 51A declares and audits the dataset. It does not run the baseline or the
locked objective. The Phase 50 final-test data are already consumed and must not
be used for tuning.

## Frozen objective

The audit requires the Phase 50B lock to remain exactly:

```yaml
reward_mode: sum
short_stem_penalty: 3.0
short_stem_length: 2
min_stem_length: 2
```

## Required CSV fields

- `sequence_id`
- `sequence`
- `reference_structure`
- `category`
- `source_name`
- `source_record_id`
- `source_url`
- `reference_method`
- `split`
- `notes`

Every research row must use `external_test` as its split.

## Integrity checks

The audit verifies:

1. the Phase 50B objective lock and Phase 50C completion tags;
2. the completed one-time final-test registry snapshot;
3. RNA alphabet and length limits;
4. unique sequence IDs, sequences, and source records;
5. valid, length-matched, pseudoknot-free dot-bracket references;
6. canonical or GU-wobble compatibility for every declared pair;
7. exact sequence leakage against prior Phase 49 and Phase 50 datasets;
8. minimum sequence, category, and length-bin coverage;
9. canonical and raw SHA-256 dataset checksums.

## Outputs

A successful audit writes:

- `dataset_snapshot.csv`
- `prior_sequence_inventory.csv`
- `leakage_report.csv`
- `dataset_profile.json`
- `audit_decision.json`
- `dataset_lock.json`
- `audit_report.md`

`dataset_lock.json` is the input contract for the later Phase 51 frozen
comparison. The dataset must not change after that lock is committed.

## Interpretation boundary

Passing this audit establishes traceability, independence from prior local test
sets, and format consistency. It does not establish biological quality,
representativeness, clinical relevance, or quantum advantage.
