# Strict Classical Foundation

## Purpose

This phase completes the strict classical benchmark bridge for the RNA-QUBO project.

The foundation supports one-sequence and 12-sequence runs:

```text
RNA input
→ ViennaRNA reference structure/energy when available
→ QUBO prediction
→ direct structure/energy comparison when available
→ saved reproducible report
```

## One-sequence command

```cmd
python -m src.evaluation.strict_classical_pipeline --sequence GGGAAAUCC --run-id professor_check_final
```

Output:

```text
results/classical_foundation/professor_check_final/
```

## Batch command

```cmd
python -m src.evaluation.run_strict_classical_batch --dataset data\external\phase51_external_dataset.csv --batch-id professor_12_sequence_check
```

Output:

```text
results/classical_foundation_batch/professor_12_sequence_check/
```

## ViennaRNA availability

Run:

```cmd
python -m src.evaluation.vienna_preflight
```

The Vienna reference layer supports:

1. RNAfold command-line executable.
2. Python ViennaRNA fallback through `import RNA`.
3. Safe unavailable status when neither method is installed.

## Important limitation

ViennaRNA MFE energy and QUBO objective value are different scoring systems. The energy comparison is diagnostic only and must not be treated as physical equivalence.

## Safe claim boundary

- No quantum advantage claim.
- No clinical accuracy claim.
- No final biological validation claim.
- The strict classical framework is a reproducible benchmark and validation layer before deeper QAOA/VQE experiments.
