# Final Submission Index — RNA-QUBO Moderna/WISER Project

## Start here

1. `README.md` — project overview, setup, and safe claims.
2. `docs/final_submission_summary.md` — final closeout summary.
3. `docs/rubric_alignment.md` — challenge rubric mapped to project evidence.
4. `docs/final_results_interpretation.md` — plain-English interpretation of results.
5. `docs/final_limitations_and_safe_claims.md` — limitations and safe claim boundary.
6. `docs/final_demo_script.md` — 3–5 minute presentation walkthrough.
7. `docs/final_professor_review_summary.md` — professor-ready summary.

## Final benchmark outputs

| Output | Path | Purpose |
|---|---|---|
| Final one-sequence report | `results/classical_foundation/final_submission_single_sequence/experiment_report.md` | Shows one complete strict-classical benchmark run. |
| Final 12-sequence summary | `results/classical_foundation_batch/final_submission_12_sequence_check/batch_summary.csv` | Professor-ready CSV table for the 12-sequence benchmark. |
| Final 12-sequence report | `results/classical_foundation_batch/final_submission_12_sequence_check/batch_report.md` | Narrative summary of batch results and limitations. |
| Final submission package | `submission_package/final_submission/` | Submission package copied into the repository. |
| Download zip | `%USERPROFILE%/Downloads/final_submission_package.zip` | Portable package for submission or sharing. |

## Core source code

| Area | Path |
|---|---|
| RNA validation and ViennaRNA reference handling | `src/classical/vienna_rnafold.py` |
| Dot-bracket utilities | `src/classical/dotbracket_tools.py` |
| Candidate generation | `src/qubo/candidate_pairs.py`, `src/qubo/candidate_stems.py` |
| QUBO construction | `src/qubo/build_qubo.py` |
| Classical solvers | `src/solvers/greedy_solver.py`, `src/solvers/simulated_annealing.py` |
| Strict classical pipeline | `src/evaluation/strict_classical_pipeline.py` |
| 12-sequence batch runner | `src/evaluation/run_strict_classical_batch.py` |
| Structural comparison | `src/evaluation/structural_comparison.py` |
| Energy diagnostics | `src/evaluation/energy_comparison.py` |
| Quantum prototypes | `src/quantum/qaoa_circuit.py`, `src/quantum/vqe_circuit.py` |
| Scaling/resource analysis | `src/evaluation/scaling.py`, `src/evaluation/hardware_readiness.py` |

## Commands for reviewers

```cmd
python -m src.evaluation.vienna_preflight
python -m src.evaluation.strict_classical_pipeline --sequence GGGAAAUCC --run-id reviewer_single_check
python -m src.evaluation.run_strict_classical_batch --dataset data\external\phase51_external_dataset.csv --batch-id reviewer_12_sequence_check
```

## Reading order for graders

Read in this order:

1. `docs/final_submission_summary.md`
2. `docs/rubric_alignment.md`
3. `results/classical_foundation_batch/final_submission_12_sequence_check/batch_report.md`
4. `results/classical_foundation_batch/final_submission_12_sequence_check/batch_summary.csv`
5. `docs/final_results_interpretation.md`
6. `docs/final_limitations_and_safe_claims.md`
