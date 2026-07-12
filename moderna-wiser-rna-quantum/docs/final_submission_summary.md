# Final Submission Summary — Moderna/WISER RNA-QUBO Project

Generated: `2026-07-12T13:16:07`
Git branch: `phase51-external-generalization`

## Submission Status

The project is complete as a reproducible RNA-QUBO strict classical benchmark and validation framework for submission review.

Completed bridge:

```text
RNA input
→ ViennaRNA reference layer / preflight status
→ candidate pair and candidate stem search space
→ stem-based QUBO formulation
→ exact, greedy, and simulated-annealing classical solvers
→ reconstructed dot-bracket prediction
→ structural and diagnostic energy comparison when ViennaRNA is available
→ runtime summary
→ one-sequence report
→ 12-sequence batch report and summary table
```

## One-Sequence Professor Check

Run ID: `final_submission_single_sequence`
Vienna success: `False`
Vienna method: `unavailable`
Reference structure: `None`
Reference energy: `None`
Predicted dot-bracket: `(((...)))`
QUBO energy: `-7.0`
Total runtime seconds: `0.04664650000631809`

## 12-Sequence Batch Check

Batch ID: `final_submission_12_sequence_check`
Sequences run: `12`
Vienna references available: `0`
Structural comparisons available: `0`
Average F1 score when available: `None`
Average runtime seconds: `0.019932475001648225`

## ViennaRNA Preflight

```text
ViennaRNA preflight check
RNAfold executable: RNAfold
RNAfold CLI available: no
ViennaRNA Python module available: no
Vienna reference status: not ready
Recommended action: Install ViennaRNA CLI or run: python -m pip install viennarna
```

## Key Output Files

- `results/classical_foundation/final_submission_single_sequence/experiment_report.md`
- `results/classical_foundation_batch/final_submission_12_sequence_check/batch_summary.csv`
- `results/classical_foundation_batch/final_submission_12_sequence_check/batch_report.md`
- `docs/strict_classical_foundation.md`
- `docs/professor_12_sequence_benchmark_plan.md`

## Safe Claim Boundary

- This project does not claim quantum advantage.
- This project does not claim clinical accuracy.
- This project does not claim final biological validation.
- ViennaRNA MFE energy and QUBO objective values are diagnostic only and are not physically equivalent scoring systems.
- If ViennaRNA CLI/Python bindings are unavailable, the framework reports that status clearly and still saves QUBO predictions and reproducibility artifacts.

## Recent Git Log

```text
48819c3 Complete strict classical benchmark validation and batch comparison
1e32082 Add strict classical foundation pipeline
3d53615 Add energy and runtime comparison utilities
208ad0d Add strict classical foundation comparison tools
ba4c924 Add ViennaRNA RNAfold wrapper
```
