# Phase 49 — QUBO Calibration and Classical Benchmarking

## Objective

Phase 49 turns the Phase 48 one-sequence pipeline into a multi-sequence,
reproducible benchmark. It separates parameter calibration from held-out
validation and records aggregate structural accuracy, solver agreement, runtime,
and QUBO scaling.

## Experimental design

The starter dataset contains 24 synthetic sequences:

- 12 calibration sequences
- 12 validation sequences
- unstructured negative controls
- designed hairpins
- wobble-enriched hairpins
- deterministic mixed-composition sequences
- lengths from 12 to 56 nucleotides

The `category` column records how a sequence was designed. ViennaRNA is still the
reference used for measured structure comparisons. The design label is not a
claim that ViennaRNA must return that intended category.

## Required order

Do not use validation results to choose parameters.

1. Run a baseline on the calibration split.
2. Run the calibration-only parameter sweep.
3. Freeze the generated `selected_strict_config.yaml`.
4. Run the held-out validation split once with that locked configuration.
5. Report both calibration and validation results, including disagreements.

## Commands

From the repository root with `.venv-phase48` activated:

```cmd
python -m pytest -q
```

### Calibration baseline

```cmd
python src\evaluation\phase49_benchmark.py --split calibration --run-id phase49_calibration_baseline_001
```

Outputs:

```text
results/phase49_benchmark/phase49_calibration_baseline_001/
```

### Parameter calibration

```cmd
python src\evaluation\phase49_parameter_sweep.py --run-id phase49_calibration_001
```

The compact grid screens:

```text
overlap_penalty: 6, 10, 14
crossing_penalty: 4, 8, 12
```

The screen uses greedy solving for speed and consistency. The top three parameter
sets are confirmed with the normal Phase 48 solver configuration.

The locked configuration is saved at:

```text
results/phase49_calibration/phase49_calibration_001/selected_strict_config.yaml
```

### Held-out validation

Run this only after calibration is complete:

```cmd
python src\evaluation\phase49_benchmark.py --split validation --strict-config results\phase49_calibration\phase49_calibration_001\selected_strict_config.yaml --run-id phase49_validation_001
```

Outputs:

```text
results/phase49_benchmark/phase49_validation_001/
```

## Benchmark outputs

Each benchmark run saves:

- `dataset_snapshot.csv`
- `effective_strict_config.yaml`
- `run_manifest.json`
- `benchmark_results.csv`
- `benchmark_summary.json`
- `metrics_by_category.csv`
- `metrics_by_length.csv`
- `solver_agreement.csv`
- `scaling_data.csv`
- `scaling_summary.json`
- `failed_runs.csv`
- `checkpoint_results.jsonl`
- `benchmark_report.md`
- one complete Phase 48 report folder per sequence under `runs/`

## Accuracy metrics

Phase 49 records:

- micro precision, recall, and F1
- macro precision, recall, and F1
- macro F1 for non-empty ViennaRNA references
- exact-structure match rate
- empty-reference accuracy
- mean and median base-pair distance
- normalized base-pair distance

The non-empty-reference metric is reported separately because all-dot controls
receive a perfect match when both methods correctly predict no base pairs.

## Solver metrics

For each sequence the benchmark records:

- exact solver status
- greedy solver status
- simulated-annealing status
- agreement of predicted structures
- agreement of QUBO objective values
- pairwise structure agreement between solvers

Solver agreement does not prove that the QUBO model is biologically correct. It
only shows whether the classical optimization methods agree on the same QUBO.

## Scaling metrics

Phase 49 records relationships among:

- sequence length
- candidate-pair count
- candidate-stem and QUBO-variable count
- quadratic-term count
- total runtime
- exact-state estimate

The generated linear fits and correlations describe only the measured benchmark
range. They are not proofs of asymptotic complexity.

## Calibration rule

Configurations are ranked lexicographically by:

1. successful-run rate
2. macro F1 on non-empty ViennaRNA references
3. micro F1
4. exact-match rate
5. lower normalized base-pair distance
6. solver structure agreement
7. lower median runtime

This avoids treating ViennaRNA MFE and QUBO objective values as equivalent.
Energy difference remains diagnostic only and is not used as a calibration target.

## Safe claim boundary

After Phase 49, the project can claim a reproducible synthetic classical
benchmark and held-out validation against ViennaRNA references. It still cannot
claim:

- experimental biological validation
- generalization to all RNA or mRNA families
- equivalence between QUBO objective and thermodynamic free energy
- quantum advantage
- superiority to ViennaRNA

A later external-validation phase should use curated public RNA datasets with
known or experimentally supported structures.
