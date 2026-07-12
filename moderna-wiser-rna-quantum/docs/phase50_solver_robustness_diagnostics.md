# Phase 50A — QUBO Solver Robustness Diagnostics

Phase 50A separates solver behavior from objective-function behavior before any
new QUBO term is introduced.

## Scientific rule

- Use only the new `development` split for diagnostics and later objective work.
- Do not use the Phase 49 validation sequences for Phase 50 tuning.
- Keep the Phase 50 `final_test` split untouched until objective refinements are locked.

## What the runner measures

For each sequence it runs exact enumeration when the QUBO has at most 20
variables, the existing greedy solver, and a multi-seed simulated-annealing
experiment. Each annealing solution is optionally refined by deterministic
one-flip descent.

Outputs include energy distributions, structure frequencies, ViennaRNA
agreement, objective decomposition, best-energy hit rate, and a diagnosis.

Exact small-QUBO labels can confirm objective or solver limitations. Large-QUBO
labels are diagnostic inferences only.

## Full development run

```cmd
python src\evaluation\phase50_solver_diagnostics.py --split development --run-id phase50_solver_diagnostics_001
```

## Outputs

Saved under `results/phase50_solver_diagnostics/<run_id>/`:

- `dataset_snapshot.csv`
- `effective_phase50_config.yaml`
- `effective_strict_config.yaml`
- `sequence_summary.csv`
- `sa_runs.csv`
- `structure_frequencies.csv`
- `energy_decomposition.csv`
- `diagnostic_summary.json`
- `diagnostic_report.md`
- `failed_runs.csv`
- per-sequence `diagnostic_detail.json`

## Safe claim boundary

This phase diagnoses the current classical QUBO and heuristic solvers. It does
not establish a global optimum for large QUBOs, biological validity, or quantum
advantage.
