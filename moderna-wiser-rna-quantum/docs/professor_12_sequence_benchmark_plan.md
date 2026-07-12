# Professor 12-Sequence Benchmark Plan

## Purpose

This plan completes the strict classical benchmark checkpoint for the RNA-QUBO project.

The goal is to run a reproducible batch comparison across 12 RNA secondary-structure sequences and produce a professor-ready summary table.

## Pipeline

Each sequence follows the same path:

```text
RNA sequence
→ ViennaRNA reference attempt
→ candidate base pairs
→ candidate stems
→ stem-based QUBO
→ exact / greedy / simulated annealing classical solvers
→ reconstructed dot-bracket structure
→ structural comparison when ViennaRNA is available
→ diagnostic energy comparison
→ saved report
```

## Dataset

The dataset file is:

```text
data/external/phase51_external_dataset.csv
```

Required columns:

```text
sequence_id
sequence
description
source
expected_use
```

## Command

```cmd
python -m src.evaluation.run_strict_classical_batch --dataset data\external\phase51_external_dataset.csv --batch-id professor_12_sequence_check
```

## Outputs

```text
results/classical_foundation_batch/professor_12_sequence_check/
```

Important files:

```text
batch_summary.csv
batch_report.md
seq_001/experiment_report.md
seq_002/experiment_report.md
...
seq_012/experiment_report.md
```

## Safe claim boundary

- This benchmark does not claim quantum advantage.
- This benchmark does not claim clinical accuracy.
- This benchmark does not claim final biological validation.
- ViennaRNA MFE energy and QUBO energy are diagnostic only and not physically equivalent.
- If ViennaRNA is unavailable, the project reports that clearly and still saves the QUBO prediction and runtime artifacts.
