# Phase 50B.1 — Equal-Budget Objective Selection Audit

## Purpose

The initial Phase 50B experiment screened seven objective variants with four
simulated-annealing seeds, then confirmed only the top three with twelve seeds.
That design was appropriate for screening, but it did not produce a direct
same-budget baseline comparison because the frozen baseline was not included in
the confirmation stage.

Phase 50B.1 compares exactly three objectives under the same computational
budget:

1. `baseline_sum`
2. `short2_penalty_3`
3. `min_stem_length_3`

Every objective uses the same 10 development sequences, 12 simulated-annealing
seeds, 6,000 steps per seed, exact-enumeration threshold, local-refinement
setting, temperature schedule, and frozen Phase 49 overlap/crossing penalties.

## Coding and methodology fixes

The audit adds two safeguards:

- **Tie-aware exact enumeration.** The exact solver records the number of
  minimum-energy assignments and captures distinct optimal structures. This
  distinguishes a uniquely wrong objective minimum from a degenerate objective
  containing both better and worse structures.
- **Safe resume.** Each variant directory stores a SHA-256 signature of the
  objective, dataset, strict configuration, exact threshold, and solver budget.
  A changed configuration cannot silently reuse stale results under the same run
  ID.

It also writes paired, per-sequence deltas against the baseline.

## Selection and locking

The ranking preserves successful execution and simple controls before comparing
mixed-sequence performance. A lock is recommended only when the selected
variant:

- completes every run;
- preserves the unstructured control and designed hairpin;
- does not reduce mixed-composition mean F1;
- does not reduce `dev_mixed_18` F1;
- remains within 0.03 micro-F1 of the baseline;
- does not increase the exact strict-failure rate;
- captures all exact-optimal structures without truncation.

A provisional configuration is always written. A `locked_objective_config.yaml`
is written only when every guardrail passes.

## Frozen-data rule

Only the `development` split is loaded. The module has no command-line option to
run the Phase 50 `final_test` split. Final-test evaluation must wait until the
equal-budget decision is reviewed, committed, and tagged.

## Interpretation boundary

The outputs measure agreement with ViennaRNA MFE references on a small synthetic
development set. They are not biological validation and do not establish quantum
advantage.
