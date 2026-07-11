# RNA-QUBO Quantum Research Project Navigation Guide

## Current Status

Current project status:

- Phase 37 complete: publication benchmark tables and figures.
- Phase 38 complete: paper package documents.
- Phase 39 complete: literature review and research gap matrix.
- Phase 40 in progress: mathematical traceability and exact validation layer.

## Project Location

`C:\Users\reyes\QuantumResearch\quantum-education-research-lab\moderna-wiser-rna-quantum`

## Open Project

```cmd
cd C:\Users\reyes\QuantumResearch\quantum-education-research-lab\moderna-wiser-rna-quantum
C:\Users\reyes\QuantumResearch\qenv\Scripts\activate
git status --short
```

## Leave These Unrelated Files Alone

```text
M ../Quantum-Communication-Dashboard/static/outputs/bell_state_histogram.png
M ../Quantum-Communication-Dashboard/static/outputs/entanglement_histogram.png
```

## Run Dashboard

```cmd
python app.py
```

Open:

`http://127.0.0.1:5000`

Stop server with `CTRL + C`.

## Main Dashboard Files

- `templates/index.html`
- `static/css/style.css`
- `static/js/app.js`

## Main Python Folders

- `src/classical`
- `src/qubo`
- `src/solvers`
- `src/evaluation`
- `src/quantum`

## Phase 37 Files

- `src/evaluation/publication_benchmark_pipeline.py`
- `results/publication_tables/final_publication_benchmark_table.csv`
- `results/publication_figures/qubo_variable_growth.png`

Run:

```cmd
python src\evaluation\publication_benchmark_pipeline.py
```

## Phase 38 Files

- `src/evaluation/publication_paper_package.py`
- `docs/paper_outline.md`
- `docs/research_problem.md`
- `docs/methodology.md`
- `docs/results_summary.md`
- `docs/novelty_questions.md`
- `docs/limitations.md`

Run:

```cmd
python src\evaluation\publication_paper_package.py
```

## Phase 39 Files

- `src/evaluation/literature_review_package.py`
- `docs/literature_review_matrix.md`
- `docs/research_gap_table.md`
- `docs/qubo_formulation_comparison.md`
- `docs/publication_references_to_collect.md`
- `results/publication_tables/literature_review_matrix.csv`

Run:

```cmd
python src\evaluation\literature_review_package.py
```

## Phase 40 Files

Phase 40 adds mathematical traceability and exact validation.

New files:

- `src/evaluation/phase40_documentation_package.py`
- `src/evaluation/exact_qubo_validator.py`
- `src/evaluation/qubo_energy_audit.py`
- `docs/mathematical_formulation.md`
- `docs/traceability_audit.md`
- `docs/exact_validation_protocol.md`
- `docs/christian_discussion_integration.md`
- `results/publication_tables/stem_traceability_table.csv`
- `results/publication_tables/exact_validation_results.csv`
- `results/publication_tables/qubo_energy_audit.csv`

Run:

```cmd
python src\evaluation\phase40_documentation_package.py
python src\evaluation\exact_qubo_validator.py
python src\evaluation\qubo_energy_audit.py
```

## Safety Wording

Use these safe claims:

- This is a prototype benchmark and feasibility framework.
- The novelty is the integrated bioinformatics-to-quantum benchmark workflow.
- The qubit-compression layer is a research extension that still requires validation.
- Current quantum results are simulator/proxy results and hardware-readiness estimates.
- The mathematical validation layer makes the QUBO model auditable before stronger claims.

Do not claim:

- quantum advantage,
- clinical accuracy,
- production RNA design readiness,
- final biological validation,
- novel QUBO formulation before literature comparison,
- compression improvement before validation.

## Daily Closeout

```cmd
git status --short
git log --oneline -5
```

<!-- PHASE41_EXACT_VALIDATION_INTEGRATION -->
# Phase 41 — Exact Validation Integration Into Final Benchmark

Purpose:

Merge exact optimum, feasibility, exact-validation notes, QUBO-to-Ising data, and energy audit summaries back into the final publication benchmark table and results summary.

Main file:

`src/evaluation/phase41_exact_validation_benchmark_integration.py`

Generated or updated files:

`results/publication_tables/final_publication_benchmark_table.csv`  
`results/publication_tables/final_publication_benchmark_table_pre_phase41_backup.csv`  
`results/publication_tables/final_publication_benchmark_with_exact_validation.csv`  
`results/publication_tables/exact_validation_integrated_summary.csv`  
`docs/phase41_exact_validation_integration.md`  
`docs/results_summary.md`  
`docs/project_navigation_guide.md`

Run:

`python src\evaluation\phase41_exact_validation_benchmark_integration.py`

Safe interpretation:

Phase 41 adds exact small-instance ground truth to the final benchmark. It supports auditability and validation, but it does not claim quantum advantage or final biological accuracy.

<!-- PHASE43_EXACT_VALIDATION_FIGURES -->
# Phase 43 — Exact Validation Publication Figures

Purpose:

Generate publication-ready figures from exact-validation outputs.

Main file:

`src/evaluation/phase43_exact_validation_figures.py`

Generated files:

`results/publication_figures/exact_minimum_energy.png`  
`results/publication_figures/exact_assignment_growth.png`  
`results/publication_figures/exact_energy_decomposition.png`  
`results/publication_figures/ising_coefficient_counts.png`  
`docs/phase43_exact_validation_figures.md`

Run:

`python src\evaluation\phase43_exact_validation_figures.py`

Safe interpretation:

Phase 43 visualizes exact small-instance validation. It supports auditability but does not claim quantum advantage or final biological accuracy.

<!-- PHASE44_GRAPH_AWARE_QRAO_VALIDATION -->
# Phase 44 — Graph-Aware QRAO Compression Validation

Purpose:

Upgrade the QRAO compression layer so it uses the QUBO interaction graph.

Main file:

`src/evaluation/phase44_graph_aware_qrao_validation.py`

Generated files:

`results/publication_tables/graph_aware_qrao_summary.csv`  
`results/publication_tables/graph_aware_qrao_mapping.csv`  
`results/publication_tables/graph_aware_qrao_conflict_check.csv`  
`results/publication_figures/graph_aware_qrao_qubit_reduction.png`  
`results/publication_figures/graph_aware_qrao_coloring_counts.png`  
`docs/phase44_graph_aware_qrao_validation.md`

Run:

`python src\evaluation\phase44_graph_aware_qrao_validation.py`

Safe interpretation:

Graph-aware QRAO validates compression mapping logic, but it does not yet prove compressed solutions preserve RNA folding quality.

<!-- PHASE45_DATASET_EXTERNAL_VALIDATION -->
# Phase 45 — Dataset and External Validation Expansion

Purpose:

Strengthen the biological validation side by adding dataset tracking and external-validation planning.

Main file:

`src/evaluation/phase45_dataset_external_validation.py`

Generated files:

`data/rna_validation_dataset.csv`  
`results/publication_tables/external_validation_dataset_tracker.csv`  
`results/publication_tables/rnafold_validation_plan.csv`  
`results/publication_tables/blast_rcsb_reference_plan.csv`  
`results/publication_tables/phase45_dataset_readiness_summary.csv`  
`results/publication_figures/dataset_sequence_lengths.png`  
`results/publication_figures/dataset_gc_content.png`  
`docs/phase45_dataset_external_validation.md`

Run:

`python src\evaluation\phase45_dataset_external_validation.py`

Safe interpretation:

Phase 45 prepares external validation tracking. It does not claim that RNAfold, BLAST, or RCSB validation has already been completed.

<!-- PHASE46_MANUSCRIPT_ASSEMBLY_PACKAGE -->
# Phase 46 — Manuscript Assembly Package

Purpose:

Assemble the current research outputs into a paper-style manuscript draft.

Main file:

`src/evaluation/phase46_manuscript_assembly_package.py`

Generated files:

`docs/manuscript/abstract.md`  
`docs/manuscript/introduction.md`  
`docs/manuscript/related_work.md`  
`docs/manuscript/methodology.md`  
`docs/manuscript/results.md`  
`docs/manuscript/discussion.md`  
`docs/manuscript/limitations.md`  
`docs/manuscript/conclusion.md`  
`docs/manuscript/future_work.md`  
`docs/manuscript/full_manuscript_draft.md`  
`docs/phase46_manuscript_assembly_package.md`  
`results/publication_tables/manuscript_key_results_summary.csv`  
`results/publication_tables/manuscript_section_source_map.csv`

Run:

`python src\evaluation\phase46_manuscript_assembly_package.py`

Safe interpretation:

Phase 46 creates a professor-review manuscript draft package. It is not a final journal submission.
