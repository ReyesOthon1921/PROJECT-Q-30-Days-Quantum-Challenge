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
