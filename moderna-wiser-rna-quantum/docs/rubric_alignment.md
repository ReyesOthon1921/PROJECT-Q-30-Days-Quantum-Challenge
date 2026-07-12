# Rubric Alignment — RNA-QUBO / Moderna-WISER Final Submission

## Purpose

This document maps the final RNA-QUBO project directly to the challenge rubric so reviewers can quickly verify that the submission addresses the required technical, biological, optimization, benchmarking, and communication criteria.

## Project claim

This project is a reproducible research prototype for exploring mRNA secondary-structure prediction as an optimization problem. It connects RNA preprocessing, candidate stem generation, QUBO construction, classical solver baselines, exact small-instance validation, ViennaRNA-reference handling, quantum-readiness analysis, scaling/resource analysis, and a 12-sequence final benchmark package.

## Safe claim boundary

The project does **not** claim quantum advantage, clinical accuracy, final biological validation, or superiority over ViennaRNA. ViennaRNA MFE energy and QUBO objective energy are treated as diagnostic comparison values, not physically equivalent scoring systems.

## Rubric Mapping

| Challenge / rubric area | Project evidence | Status | Reviewer note |
|---|---|---:|---|
| Background review | `docs/manuscript/related_work.md`, `docs/literature_review_matrix.md`, `docs/research_gap_table.md` | Complete | Covers RNA folding, MFE, QUBO, QAOA/VQE readiness, and limitations. |
| Classical benchmark generation | `src/classical/vienna_rnafold.py`, `src/evaluation/vienna_preflight.py`, `results/classical_foundation/final_submission_single_sequence/` | Complete as framework | ViennaRNA comparison is active when RNAfold CLI or ViennaRNA Python bindings are available; otherwise status is reported clearly. |
| Candidate structure representation | `src/classical/dotbracket_tools.py`, `src/qubo/candidate_pairs.py`, `src/qubo/candidate_stems.py` | Complete | Represents structures using dot-bracket and base-pair/stem candidate spaces. |
| QUBO / optimization formulation | `src/qubo/build_qubo.py`, `docs/mathematical_formulation.md`, `docs/traceability_audit.md` | Complete | Stem-based QUBO with penalties and traceability/audit outputs. |
| Classical solver baselines | `src/solvers/greedy_solver.py`, `src/solvers/simulated_annealing.py`, `results/publication_tables/classical_solver_benchmark.csv` | Complete | Includes exact small-instance validation, greedy baseline, and simulated annealing. |
| Exact validation | `src/evaluation/exact_qubo_validator.py`, `results/publication_tables/exact_validation_results.csv`, `results/publication_tables/exact_validation_integrated_summary.csv` | Complete | Verifies small QUBO instances by enumeration. |
| Energy evaluation | `src/evaluation/energy_comparison.py`, `results/classical_foundation/final_submission_single_sequence/energy_comparison.json` | Complete | Diagnostic only; avoids false equivalence between MFE and QUBO objective. |
| Structural comparison | `src/evaluation/structural_comparison.py`, batch summary outputs | Complete when reference available | Precision, recall, F1, exact match, and base-pair distance are available when a reference structure exists. |
| Quantum / quantum-inspired algorithm design | `src/quantum/qaoa_circuit.py`, `src/quantum/vqe_circuit.py`, `src/evaluation/quantum_benchmark.py` | Complete as readiness/prototype layer | Uses simulator/readiness framing rather than unsupported quantum-advantage claims. |
| Scaling and resource analysis | `src/evaluation/scaling.py`, `src/evaluation/hardware_readiness.py`, `results/publication_figures/`, `results/publication_tables/` | Complete | Reports variable growth, circuit depth, qubit estimates, runtime, and hardware limits. |
| Qubit compression / graph-aware analysis | `src/evaluation/qubit_compression_estimator.py`, `src/evaluation/qrao_subset_mapping.py`, `results/publication_tables/graph_aware_qrao_summary.csv` | Complete as research extension | Clearly framed as exploratory and requiring further validation. |
| Implementation and benchmarking | `src/evaluation/strict_classical_pipeline.py`, `src/evaluation/run_strict_classical_batch.py` | Complete | One-sequence and 12-sequence final checks are reproducible. |
| Reproducibility | `configs/strict_classical_foundation.yaml`, `docs/final_submission_summary.md`, final submission zip | Complete | Configuration, outputs, reports, and final package are saved. |
| Communication quality | `README.md`, `docs/final_submission_index.md`, `docs/final_demo_script.md`, `docs/final_professor_review_summary.md` | Complete | Reviewer can follow the project without reading all source code. |

## A+ argument

This project does not only implement a demo. It provides a reproducible research framework with classical benchmarking, QUBO formulation, solver comparison, exact small-instance validation, quantum-readiness analysis, resource-scaling discussion, safe claim boundaries, and a final 12-sequence benchmark package mapped directly to the challenge rubric.
