# Strict Classical Foundation

## Goal

One command takes an RNA sequence and saves a reproducible classical benchmark report:

```text
RNA input
→ automatic ViennaRNA/RNAfold reference
→ candidate base-pair/stem search space
→ stem-based QUBO formulation
→ classical solver result
→ reconstructed dot-bracket structure
→ structural comparison
→ diagnostic energy comparison
→ runtime summary
→ saved report
```

## Run

```cmd
python src\evaluation\strict_classical_pipeline.py --sequence GGGAAAUCC --run-id phase48_smoke_test
```

Outputs are saved in:

```text
results/classical_foundation/phase48_smoke_test/
```

## Required Outputs

- `input_sequence.txt`
- `vienna_reference.json`
- `candidate_pairs.csv`
- `candidate_stems.csv`
- `qubo_summary.csv`
- `solver_results.csv`
- `predicted_structure.json`
- `structural_comparison.json`
- `energy_comparison.json`
- `runtime_summary.json`
- `experiment_report.md`
- `artifact_manifest.csv`

## Safe Claim Boundary

This foundation does not claim quantum advantage, clinical accuracy, or final biological validation. ViennaRNA MFE and QUBO objective values are diagnostic only and are not physically equivalent scoring systems.
