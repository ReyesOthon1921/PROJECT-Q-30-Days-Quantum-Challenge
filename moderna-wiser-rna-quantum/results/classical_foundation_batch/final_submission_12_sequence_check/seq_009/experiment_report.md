# Strict Classical Foundation Experiment Report — seq_009

## Purpose

This report records one reproducible classical RNA-QUBO benchmark run.

## Run Metadata

- Run ID: `seq_009`
- Timestamp: `2026-07-12T13:16:06`
- Input sequence: `GGGCUAAAGCCC`

## ViennaRNA Reference

- RNAfold success: `False`
- Vienna method: `unavailable`
- Reference structure: `Not available`
- Reference energy: `Not available`
- Runtime seconds: `0.0040166999970097095`
- Error: `ViennaRNA reference unavailable. CLI error: RNAfold command was not found. Install ViennaRNA or add RNAfold to PATH. Python fallback error: ViennaRNA Python RNA.fold returned an unexpected value.`

## Predicted Structure

- Predicted dot-bracket: `((((....))))`
- Predicted pairs: `[(0, 11), (1, 10), (2, 9), (3, 8)]`
- Solver used: `exact`
- QUBO energy: `-12.0`

## Structural Comparison

- Comparison available: `False`
- Exact match: `Not available`
- Precision: `Not available`
- Recall: `Not available`
- F1 score: `Not available`
- Base-pair distance: `Not available`

## Diagnostic Energy Comparison

- Comparison available: `False`
- ViennaRNA reference energy: `Not available`
- QUBO energy: `-12.0`
- Energy difference: `Not available`
- Absolute energy difference: `Not available`

Important note: ViennaRNA MFE energy and QUBO energy are different scoring systems. This comparison is diagnostic only and should not be treated as physical equivalence.

## Runtime Summary

- Step count: `5`
- Total runtime seconds: `0.023898799991002306`
- Slowest step: `solver_execution`

## Safe Claim Boundary

- This run does not claim quantum advantage.
- This run does not claim clinical accuracy.
- This run does not claim final biological validation.
- This run supports a reproducible classical benchmark bridge before deeper QAOA/VQE work.

## Configuration Snapshot

```json
{
  "sequence": "GGGAAAUCC",
  "min_loop_length": 3,
  "allow_wobble": true,
  "candidate_mode": "stems",
  "stem_min_length": 2,
  "overlap_penalty": 10.0,
  "crossing_penalty": 8.0,
  "solver_exact_max_variables": 20,
  "run_greedy": true,
  "run_simulated_annealing": true,
  "simulated_annealing_steps": 8000,
  "simulated_annealing_initial_temperature": 10.0,
  "simulated_annealing_final_temperature": 0.01,
  "simulated_annealing_cooling_rate": 0.995,
  "random_seed": 7,
  "rnafold_executable": "RNAfold",
  "allow_vienna_python_fallback": true,
  "notes": "Strict classical foundation integrated with the project's existing candidate-pair, candidate-stem, QUBO, greedy, and simulated-annealing code. ViennaRNA MFE and QUBO objective values are diagnostic only and are not physically equivalent scoring systems.\n"
}
```
