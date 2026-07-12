# Final Project Audit Report

Generated: `2026-07-12T13:48:15`

## Overall Status

**Audit status:** `PASS`

This audit checks the final Moderna/WISER RNA-QUBO submission package, including the strict classical pipeline, final 12-sequence benchmark outputs, A+ evidence documents, and safe-claim documentation.

## Repository State

- Branch: `phase51-external-generalization`
- Recent commits:

```text
4830a49 Add final submission package
48819c3 Complete strict classical benchmark validation and batch comparison
1e32082 Add strict classical foundation pipeline
3d53615 Add energy and runtime comparison utilities
208ad0d Add strict classical foundation comparison tools
```

## Validation Results

- Required project files present: `True`
- Tests passed: `True`
- 12-sequence batch available: `True`
- Dataset has at least 12 records: `True`
- Selected batch summary: `results/classical_foundation_batch/a_plus_12_sequence_check/batch_summary.csv`
- Batch sequence count: `12`
- Dataset sequence count: `12`
- Vienna successes in selected batch: `0`
- Structural comparisons available in selected batch: `0`
- Average F1 score when available: `Not available`
- Average runtime seconds: `0.0204`
- Dataset categories: `Not available`

## Pytest Output

Command: `C:\Users\reyes\QuantumResearch\quantum-education-research-lab\moderna-wiser-rna-quantum\.venv-phase48\Scripts\python.exe -m pytest tests/test_vienna_rnafold.py tests/test_dotbracket_tools.py tests/test_structural_comparison.py tests/test_energy_comparison.py tests/test_runtime_summary.py tests/test_experiment_report_writer.py tests/test_strict_classical_pipeline.py tests/test_vienna_preflight.py tests/test_run_strict_classical_batch.py -q`

```text
....................................                                     [100%]
36 passed in 0.43s


```

## ViennaRNA Preflight Output

Command: `C:\Users\reyes\QuantumResearch\quantum-education-research-lab\moderna-wiser-rna-quantum\.venv-phase48\Scripts\python.exe -m src.evaluation.vienna_preflight`

```text
ViennaRNA preflight check
RNAfold executable: RNAfold
RNAfold CLI available: no
ViennaRNA Python module available: yes
Vienna reference status: ready
Recommended action: ViennaRNA reference layer is ready. Run the strict classical pipeline.


```

## Final Evidence Files

| Status | File | Purpose | Size |
|---|---|---|---:|
| PASS | `README.md` | Project landing page | 2131 |
| PASS | `docs/final_submission_summary.md` | Final submission summary | 2768 |
| PASS | `docs/rubric_alignment.md` | Challenge rubric alignment | 4913 |
| PASS | `docs/final_submission_index.md` | Reviewer navigation index | 3062 |
| PASS | `docs/final_results_interpretation.md` | Plain-English result interpretation | 3062 |
| PASS | `docs/final_limitations_and_safe_claims.md` | Safe claims and limitations | 2315 |
| PASS | `docs/final_demo_script.md` | Final demo script | 2521 |
| PASS | `docs/final_professor_review_summary.md` | Professor review summary | 1988 |
| PASS | `docs/strict_classical_foundation.md` | Strict classical pipeline documentation | 1555 |
| PASS | `docs/professor_12_sequence_benchmark_plan.md` | 12-sequence benchmark plan | 1647 |
| PASS | `src/evaluation/strict_classical_pipeline.py` | One-sequence strict classical pipeline | 17338 |
| PASS | `src/evaluation/run_strict_classical_batch.py` | 12-sequence batch runner | 9937 |
| PASS | `src/evaluation/vienna_preflight.py` | ViennaRNA preflight check | 1495 |
| PASS | `data/external/phase51_external_dataset.csv` | 12-sequence dataset | 822 |
| PASS | `results/classical_foundation/final_submission_single_sequence/experiment_report.md` | Final one-sequence report | 2784 |
| PASS | `results/classical_foundation/professor_check_final/experiment_report.md` | Professor one-sequence report | 2764 |
| PASS | `results/classical_foundation_batch/final_submission_12_sequence_check/batch_summary.csv` | Final 12-sequence batch summary | 2221 |
| PASS | `results/classical_foundation_batch/final_submission_12_sequence_check/batch_report.md` | Final 12-sequence batch report | 848 |
| PASS | `results/classical_foundation_batch/a_plus_12_sequence_check/batch_summary.csv` | A+ 12-sequence batch summary | 2223 |
| PASS | `results/classical_foundation_batch/a_plus_12_sequence_check/batch_report.md` | A+ 12-sequence batch report | 837 |
| PASS | `results/final_submission/final_evidence_manifest.csv` | Final evidence manifest | 2496 |
| PASS | `results/final_submission/final_grade_audit.csv` | Final grade audit | 2091 |

## Safe Claim Boundary

- This project does not claim quantum advantage.
- This project does not claim clinical accuracy.
- This project does not claim final biological validation.
- ViennaRNA MFE energy and QUBO objective values are diagnostic comparison values only and are not physically equivalent scoring systems.
- The project is best presented as a reproducible classical-to-quantum RNA-QUBO research prototype and benchmark framework.

## Submission Interpretation

The project is submission-ready when this audit status is `PASS`. If the status is `CHECK`, review the table above for missing or empty evidence files. ViennaRNA availability may vary by local environment; the framework records that status instead of crashing.

## Current Git Status

```text
M ../Quantum-Communication-Dashboard/static/outputs/bell_state_histogram.png
 M ../Quantum-Communication-Dashboard/static/outputs/entanglement_histogram.png
A  docs/final_demo_script.md
A  docs/final_limitations_and_safe_claims.md
A  docs/final_professor_review_summary.md
A  docs/final_results_interpretation.md
A  docs/final_submission_index.md
A  docs/rubric_alignment.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/batch_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/batch_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_001/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_002/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_003/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_004/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_005/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_006/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_007/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_008/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_009/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_010/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_011/vienna_reference.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/artifact_manifest.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/candidate_pairs.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/candidate_stems.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/config_snapshot.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/energy_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/experiment_report.md
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/input_sequence.txt
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/predicted_structure.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/qubo_summary.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/runtime_summary.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/solver_results.csv
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/structural_comparison.json
A  results/classical_foundation_batch/a_plus_12_sequence_check/seq_012/vienna_reference.json
A  results/final_submission/final_evidence_manifest.csv
A  results/final_submission/final_grade_audit.csv
?? ../criptsa_plus_evidence_validate_commit_push.bat
?? "../e48) C\357\200\272Usersreyes...moderna-wiser-rna-quantum\357\200\276"
?? APLUS_EVIDENCE_README.md
?? AUDIT_REPORT_FIX_README.md
?? _final_audit_report_generator.py
?? data/external/phase51_source_intake.txt
?? docs/final_project_audit_report.md
?? final_project_audit_bundle/
?? run_final_project_audit_report_fix.bat
?? scripts/
```
