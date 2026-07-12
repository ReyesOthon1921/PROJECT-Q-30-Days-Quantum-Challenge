# Phase 48 — Strict Classical Foundation

## Integration approach

This Phase 48 layer **reuses the project's existing code**:

- `src/classical/sequence_tools.py`
- `src/classical/dotbracket.py`
- `src/qubo/candidate_pairs.py`
- `src/qubo/candidate_stems.py`
- `src/qubo/build_qubo.py`
- `src/solvers/greedy_solver.py`
- `src/solvers/simulated_annealing.py`

It adds a strict ViennaRNA reference wrapper, exact enumeration for small
instances, standardized structural and energy comparisons, and reproducible run
outputs. It does not replace the quantum prototype layers.

## Run one sequence

From the `moderna-wiser-rna-quantum` project root:

```cmd
python src\evaluation\strict_classical_pipeline.py --sequence GGGAAAUCC --run-id test_001
```

The default configuration is:

```text
configs/strict_classical_foundation.yaml
```

## ViennaRNA backends

The wrapper attempts:

1. `RNAfold --noPS` through `subprocess`
2. the existing ViennaRNA Python binding `RNA.fold` as a Windows-friendly fallback

The JSON result records the backend actually used. If neither backend is
available, all QUBO and solver outputs are still saved, but the command exits
with code `2` because the strict reference comparison is incomplete.

## Saved outputs

```text
results/classical_foundation/<run_id>/
    input_sequence.txt
    vienna_reference.json
    candidate_pairs.csv
    candidate_stems.csv
    qubo_summary.csv
    solver_results.csv
    predicted_structure.json
    structural_comparison.json
    energy_comparison.json
    runtime_summary.json
    experiment_report.md
```

## Solver selection

The pipeline runs exact enumeration when the QUBO is at or below the configured
variable limit. It also runs the project's greedy and simulated-annealing
solvers. The prediction with the lowest QUBO objective is selected; exact
enumeration wins ties because it certifies the global minimum for the enumerated
model.

## Interpretation boundary

ViennaRNA MFE is a thermodynamic free-energy estimate. The project QUBO is a
heuristic stem-selection objective. Their values are saved side by side only as
a diagnostic and are not the same physical quantity.

A completed run demonstrates a reproducible classical benchmark pipeline. It
does not prove quantum advantage or experimental biological validity.
