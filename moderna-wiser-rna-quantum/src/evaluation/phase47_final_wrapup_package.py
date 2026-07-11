from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]

DOCS_DIR = ROOT / "docs"
TABLE_DIR = ROOT / "results" / "publication_tables"
FIGURE_DIR = ROOT / "results" / "publication_figures"
MANUSCRIPT_DIR = DOCS_DIR / "manuscript"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

README_PATH = ROOT / "README.md"

FINAL_HANDOFF_DOC = DOCS_DIR / "final_project_handoff_package.md"
FINAL_DEMO_SCRIPT_DOC = DOCS_DIR / "final_dashboard_demo_script_phase47.md"
FINAL_DEPLOYMENT_DOC = DOCS_DIR / "final_deployment_checklist_phase47.md"
PROFESSOR_PACKET_DOC = DOCS_DIR / "professor_review_packet.md"
PHASE47_DOC = DOCS_DIR / "phase47_final_wrapup_package.md"

PROJECT_MANIFEST_TABLE = TABLE_DIR / "final_project_manifest.csv"
PHASE_COMPLETION_TABLE = TABLE_DIR / "final_phase_completion_summary.csv"

RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"

PHASE47_MARKER = "<!-- PHASE47_FINAL_WRAPUP_PACKAGE -->"

GITHUB_REPO = "https://github.com/ReyesOthon1921/PROJECT-Q-30-Days-Quantum-Challenge"
LIVE_DASHBOARD = "https://moderna-wiser-rna-quantum.onrender.com"


KEY_FILES = [
    ("Application", "app.py", "Main Flask dashboard application."),
    ("Application", "wsgi.py", "Render/Gunicorn entry point."),
    ("Application", "Procfile", "Deployment start command file."),
    ("Application", "requirements-deploy.txt", "Deployment dependency list."),
    ("Dashboard", "templates/index.html", "Main dashboard HTML."),
    ("Dashboard", "static/css/style.css", "Dashboard styling."),
    ("Dashboard", "static/js/app.js", "Dashboard frontend logic."),
    ("Classical RNA", "src/classical/dotbracket.py", "Dot-bracket validation and parsing."),
    ("Classical RNA", "src/classical/sequence_tools.py", "RNA sequence preprocessing."),
    ("QUBO", "src/qubo/candidate_pairs.py", "Candidate base-pair generation."),
    ("QUBO", "src/qubo/candidate_stems.py", "Candidate stem generation."),
    ("QUBO", "src/qubo/build_qubo.py", "Stem-based QUBO construction."),
    ("Solvers", "src/solvers/greedy_solver.py", "Greedy QUBO solver."),
    ("Solvers", "src/solvers/simulated_annealing.py", "Simulated annealing solver."),
    ("Evaluation", "src/evaluation/exact_qubo_validator.py", "Exact small-instance QUBO validator."),
    ("Evaluation", "src/evaluation/qubo_energy_audit.py", "Term-by-term QUBO energy audit."),
    ("Evaluation", "src/evaluation/phase41_exact_validation_benchmark_integration.py", "Exact-validation benchmark integration."),
    ("Evaluation", "src/evaluation/exact_validation_dashboard.py", "Exact-validation dashboard API data module."),
    ("Evaluation", "src/evaluation/phase43_exact_validation_figures.py", "Exact-validation publication figures."),
    ("Evaluation", "src/evaluation/phase44_graph_aware_qrao_validation.py", "Graph-aware QRAO validation."),
    ("Evaluation", "src/evaluation/phase45_dataset_external_validation.py", "Dataset and external-validation planning."),
    ("Evaluation", "src/evaluation/phase46_manuscript_assembly_package.py", "Manuscript assembly package."),
    ("Manuscript", "docs/manuscript/full_manuscript_draft.md", "Full manuscript draft."),
    ("Results", "results/publication_tables/final_publication_benchmark_with_exact_validation.csv", "Final benchmark with exact validation."),
    ("Results", "results/publication_tables/exact_validation_integrated_summary.csv", "Exact-validation integrated summary."),
    ("Results", "results/publication_tables/graph_aware_qrao_summary.csv", "Graph-aware QRAO summary."),
    ("Results", "results/publication_tables/phase45_dataset_readiness_summary.csv", "Dataset readiness summary."),
    ("Figures", "results/publication_figures/exact_minimum_energy.png", "Exact minimum energy figure."),
    ("Figures", "results/publication_figures/exact_assignment_growth.png", "Exact assignment growth figure."),
    ("Figures", "results/publication_figures/exact_energy_decomposition.png", "Exact energy decomposition figure."),
    ("Figures", "results/publication_figures/ising_coefficient_counts.png", "Ising coefficient count figure."),
    ("Figures", "results/publication_figures/graph_aware_qrao_qubit_reduction.png", "Graph-aware QRAO qubit-reduction figure."),
    ("Figures", "results/publication_figures/graph_aware_qrao_coloring_counts.png", "Graph-aware QRAO coloring-count figure."),
    ("Figures", "results/publication_figures/dataset_sequence_lengths.png", "Dataset sequence-length figure."),
    ("Figures", "results/publication_figures/dataset_gc_content.png", "Dataset GC-content figure."),
]


PHASES = [
    ("Phase 0", "Project setup", "Complete"),
    ("Phase 1", "Classical RNA foundation", "Complete"),
    ("Phase 2", "Flask dashboard foundation", "Complete"),
    ("Phase 3", "Sequence preprocessing", "Complete"),
    ("Phase 4", "Classical benchmark direction", "Complete"),
    ("Phase 5", "Candidate pair and stem generation", "Complete"),
    ("Phase 6", "Stem-based QUBO builder", "Complete"),
    ("Phase 7", "Greedy solver", "Complete"),
    ("Phase 8", "Evaluation metrics", "Complete"),
    ("Phase 9", "Scaling analysis", "Complete"),
    ("Phase 10", "Demo script", "Complete"),
    ("Phase 11", "Simulated annealing", "Complete"),
    ("Phase 12", "Solver comparison", "Complete"),
    ("Phase 13", "Documentation packaging", "Complete"),
    ("Phase 14", "Professional UI and RNA visualization", "Complete"),
    ("Phase 15", "Summary cards and results display", "Complete"),
    ("Phase 16", "QAOA readiness", "Complete"),
    ("Phase 17", "VQE readiness", "Complete"),
    ("Phase 18", "Deployment prep", "Complete"),
    ("Phase 19", "Scaling graphs", "Complete"),
    ("Phase 20", "Algorithm comparison graphs", "Complete"),
    ("Phase 22", "Bioinformatics metrics and resource layer", "Complete"),
    ("Phase 23", "Quantum benchmark layer", "Complete"),
    ("Phase 25", "QAOA circuit prototype", "Complete"),
    ("Phase 26", "VQE circuit prototype", "Complete"),
    ("Phase 27", "QAOA vs VQE circuit comparison", "Complete"),
    ("Phase 28", "Quantum circuit report", "Complete"),
    ("Phase 29", "QAOA parameter sweep", "Complete"),
    ("Phase 30", "VQE parameter sweep", "Complete"),
    ("Phase 31", "Measured bitstring energy", "Complete"),
    ("Phase 32", "Hardware readiness", "Complete"),
    ("Phase 33-35", "Variable compression research layer", "Complete"),
    ("Phase 36", "Guided research workbench", "Complete"),
    ("Phase 37", "Publication benchmark tables and figures", "Complete"),
    ("Phase 38", "Publication paper package", "Complete"),
    ("Phase 39", "Literature review and research gap matrix", "Complete"),
    ("Phase 40", "Mathematical traceability and exact validation", "Complete"),
    ("Phase 41", "Exact validation integration into final benchmark", "Complete"),
    ("Phase 42", "Dashboard integration for exact validation", "Complete"),
    ("Phase 43", "Exact-validation publication figures", "Complete"),
    ("Phase 44", "Graph-aware QRAO compression validation", "Complete"),
    ("Phase 45", "Dataset and external-validation expansion", "Complete"),
    ("Phase 46", "Manuscript assembly package", "Complete"),
    ("Phase 47", "Final dashboard, README, demo, and deployment polish", "Complete"),
]


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames: List[str] = []

    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_doc(path: Path, lines: List[str]) -> None:
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def file_status(relative_path: str) -> Dict[str, Any]:
    path = ROOT / relative_path

    return {
        "path": relative_path,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def build_project_manifest() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for category, relative_path, description in KEY_FILES:
        status = file_status(relative_path)

        rows.append(
            {
                "category": category,
                "path": relative_path,
                "exists": status["exists"],
                "size_bytes": status["size_bytes"],
                "description": description,
            }
        )

    return rows


def build_phase_completion_summary() -> List[Dict[str, Any]]:
    return [
        {
            "phase": phase,
            "name": name,
            "status": status,
            "note": "Included in final prototype package.",
        }
        for phase, name, status in PHASES
    ]


def count_table_rows(path: Path) -> int:
    return len(read_csv(path))


def write_project_readme() -> None:
    lines = [
        "# RNA-QUBO Quantum Research Prototype",
        "",
        "## Project Summary",
        "",
        "This project is an end-to-end RNA secondary-structure optimization research prototype.",
        "",
        "It connects bioinformatics preprocessing, candidate pair/stem generation, stem-based QUBO formulation, classical solvers, exact small-instance validation, QUBO-to-Ising conversion, QAOA/VQE feasibility modules, graph-aware QRAO compression validation, dashboard visualization, and manuscript preparation.",
        "",
        "## Live Dashboard",
        "",
        LIVE_DASHBOARD,
        "",
        "## GitHub Repository",
        "",
        GITHUB_REPO,
        "",
        "## Current Status",
        "",
        "Phase 47 complete: final dashboard, README, demo, deployment, and handoff package.",
        "",
        "## How to Run Locally",
        "",
        "```cmd",
        "cd C:\\Users\\reyes\\QuantumResearch\\quantum-education-research-lab\\moderna-wiser-rna-quantum",
        "C:\\Users\\reyes\\QuantumResearch\\qenv\\Scripts\\activate",
        "python app.py",
        "```",
        "",
        "Open:",
        "",
        "```text",
        "http://127.0.0.1:5000",
        "```",
        "",
        "## Key API Endpoint",
        "",
        "```text",
        "/api/exact-validation-dashboard",
        "```",
        "",
        "This endpoint returns exact-validation, energy-audit, QUBO-to-Ising, and benchmark integration data.",
        "",
        "## Main Research Outputs",
        "",
        "- `docs/manuscript/full_manuscript_draft.md`",
        "- `docs/final_project_handoff_package.md`",
        "- `docs/final_dashboard_demo_script_phase47.md`",
        "- `results/publication_tables/final_publication_benchmark_with_exact_validation.csv`",
        "- `results/publication_tables/final_project_manifest.csv`",
        "- `results/publication_tables/final_phase_completion_summary.csv`",
        "",
        "## Safe Research Claim",
        "",
        "This project is a prototype benchmark and feasibility framework.",
        "",
        "It does not claim quantum advantage, clinical accuracy, production RNA design readiness, final biological validation, or proven compression improvement.",
        "",
        "The contribution is an integrated and auditable workflow connecting RNA preprocessing, QUBO modeling, exact validation, quantum-readiness analysis, graph-aware compression analysis, and publication preparation.",
        "",
        "## Next Human Review Step",
        "",
        "Review with the professor before making publication, novelty, or biological-performance claims.",
    ]

    write_doc(README_PATH, lines)


def write_final_handoff_doc() -> None:
    manifest_count = len(KEY_FILES)
    benchmark_rows = count_table_rows(TABLE_DIR / "final_publication_benchmark_with_exact_validation.csv")
    exact_rows = count_table_rows(TABLE_DIR / "exact_validation_integrated_summary.csv")
    qrao_rows = count_table_rows(TABLE_DIR / "graph_aware_qrao_summary.csv")
    manuscript_exists = (MANUSCRIPT_DIR / "full_manuscript_draft.md").exists()

    lines = [
        "# Final Project Handoff Package",
        "",
        "## Project Title",
        "",
        "RNA Secondary Structure Prediction and Optimization Using QUBO, Classical and Quantum Algorithms with Qubit Compression",
        "",
        "## Current Status",
        "",
        "The prototype and publication-preparation package is complete through Phase 47.",
        "",
        "## What Is Complete",
        "",
        "- Flask dashboard",
        "- Render deployment preparation",
        "- RNA preprocessing layer",
        "- Candidate pair and stem generation",
        "- Stem-based QUBO builder",
        "- Greedy and simulated annealing baselines",
        "- QAOA/VQE readiness and circuit prototype layers",
        "- Measured bitstring energy layer",
        "- Hardware-readiness checks",
        "- Mathematical traceability documentation",
        "- Exact small-instance validation",
        "- QUBO energy audit",
        "- QUBO-to-Ising coefficient export",
        "- Exact-validation dashboard integration",
        "- Publication figures",
        "- Graph-aware QRAO compression validation",
        "- Dataset and external-validation planning",
        "- Manuscript assembly package",
        "- Final README and demo/deployment checklist",
        "",
        "## Current Counts",
        "",
        f"- Key files tracked in final manifest: {manifest_count}",
        f"- Final benchmark rows with exact validation: {benchmark_rows}",
        f"- Exact-validation integrated summary rows: {exact_rows}",
        f"- Graph-aware QRAO summary rows: {qrao_rows}",
        f"- Full manuscript draft exists: {manuscript_exists}",
        "",
        "## Main Files for Review",
        "",
        "- `README.md`",
        "- `docs/manuscript/full_manuscript_draft.md`",
        "- `docs/professor_review_packet.md`",
        "- `docs/final_dashboard_demo_script_phase47.md`",
        "- `docs/final_deployment_checklist_phase47.md`",
        "- `results/publication_tables/final_publication_benchmark_with_exact_validation.csv`",
        "- `results/publication_tables/final_project_manifest.csv`",
        "- `results/publication_tables/final_phase_completion_summary.csv`",
        "",
        "## Live Dashboard",
        "",
        LIVE_DASHBOARD,
        "",
        "## GitHub Repository",
        "",
        GITHUB_REPO,
        "",
        "## Safe Claim Boundary",
        "",
        "This is a prototype benchmark and feasibility framework.",
        "",
        "Do not claim quantum advantage, clinical accuracy, final biological validation, or proven compression improvement before professor review and additional validation.",
    ]

    write_doc(FINAL_HANDOFF_DOC, lines)


def write_demo_script() -> None:
    lines = [
        "# Final Dashboard Demo Script — Phase 47",
        "",
        "## Goal",
        "",
        "Use this script to explain the project clearly during professor review or a research demo.",
        "",
        "## 1. Opening",
        "",
        "This project is an RNA-QUBO quantum research prototype. It studies how RNA secondary-structure prediction can be represented as an optimization problem and evaluated through classical solvers, quantum-readiness modules, exact validation, and compression analysis.",
        "",
        "## 2. Dashboard Link",
        "",
        LIVE_DASHBOARD,
        "",
        "## 3. Demo Flow",
        "",
        "### Step 1 — RNA Input",
        "",
        "Show the RNA sequence input and explain that the pipeline starts with cleaned RNA sequences.",
        "",
        "### Step 2 — Candidate Pairs and Stems",
        "",
        "Explain that candidate base pairs and candidate stems become the structural building blocks for the QUBO model.",
        "",
        "### Step 3 — Stem-Based QUBO",
        "",
        "Explain that each candidate stem becomes a binary variable. Linear terms reward favorable stems, while quadratic terms penalize invalid combinations.",
        "",
        "### Step 4 — Classical Solvers",
        "",
        "Show greedy and simulated annealing as baseline solvers.",
        "",
        "### Step 5 — Quantum Readiness",
        "",
        "Explain QAOA/VQE readiness as feasibility analysis, not proof of quantum advantage.",
        "",
        "### Step 6 — Exact Validation Dashboard",
        "",
        "Show exact minimum energy, feasibility, best bitstring, decoded dot-bracket structure, QUBO-to-Ising summary, and energy audit summary.",
        "",
        "### Step 7 — Graph-Aware QRAO",
        "",
        "Explain that graph-aware QRAO uses the QUBO interaction graph to avoid packing interacting variables into the same compressed qubit.",
        "",
        "### Step 8 — Publication Package",
        "",
        "Show manuscript draft, results tables, and publication figures.",
        "",
        "## 4. Safe Closing",
        "",
        "The current contribution is an integrated and auditable research framework. The project does not claim quantum advantage or final biological validation yet.",
    ]

    write_doc(FINAL_DEMO_SCRIPT_DOC, lines)


def write_deployment_checklist() -> None:
    lines = [
        "# Final Deployment Checklist — Phase 47",
        "",
        "## Local Test",
        "",
        "Run:",
        "",
        "```cmd",
        "python app.py",
        "```",
        "",
        "Open:",
        "",
        "```text",
        "http://127.0.0.1:5000",
        "```",
        "",
        "Test API:",
        "",
        "```text",
        "http://127.0.0.1:5000/api/exact-validation-dashboard",
        "```",
        "",
        "Expected:",
        "",
        "```text",
        "\"success\": true",
        "```",
        "",
        "## GitHub Check",
        "",
        "Run:",
        "",
        "```cmd",
        "git log --oneline -5",
        "git status --short",
        "```",
        "",
        "Only the unrelated Quantum-Communication-Dashboard files should remain modified.",
        "",
        "## Render Deploy",
        "",
        "1. Open Render.",
        "2. Open `moderna-wiser-rna-quantum` service.",
        "3. Click `Manual Deploy`.",
        "4. Click `Deploy latest commit`.",
        "5. Wait until deploy finishes.",
        "6. Open the live dashboard.",
        "7. Hard refresh with `CTRL + F5`.",
        "",
        "Live dashboard:",
        "",
        LIVE_DASHBOARD,
        "",
        "Live API test:",
        "",
        f"{LIVE_DASHBOARD}/api/exact-validation-dashboard",
        "",
        "## Safe Final Status",
        "",
        "After deployment, the prototype package is complete for professor review.",
    ]

    write_doc(FINAL_DEPLOYMENT_DOC, lines)


def write_professor_packet() -> None:
    lines = [
        "# Professor Review Packet",
        "",
        "## Summary Message",
        "",
        "Hello Professor,",
        "",
        "I wanted to give you a clear update. I completed the full prototype and publication-preparation package through Phase 47.",
        "",
        "The project now includes the RNA/QUBO dashboard, classical solver baselines, QAOA/VQE feasibility layers, exact small-instance validation, QUBO-to-Ising coefficient export, term-by-term QUBO energy auditing, graph-aware QRAO compression validation, dataset/external-validation planning, publication figures, and a manuscript draft package.",
        "",
        "I also added a final handoff package, dashboard demo script, deployment checklist, README, project manifest, and phase-completion summary.",
        "",
        "The strongest current contribution is the integrated and auditable bioinformatics-to-quantum benchmark framework. I am still being careful not to claim quantum advantage, clinical accuracy, final biological validation, or proven compression improvement.",
        "",
        "The next step is professor review so we can decide what needs to be strengthened before treating this as a publication manuscript.",
        "",
        "Thank you again for your guidance.",
        "",
        "## Review Links",
        "",
        f"- Live dashboard: {LIVE_DASHBOARD}",
        f"- GitHub repository: {GITHUB_REPO}",
        "",
        "## Suggested Review Order",
        "",
        "1. `README.md`",
        "2. `docs/final_project_handoff_package.md`",
        "3. `docs/manuscript/full_manuscript_draft.md`",
        "4. `results/publication_tables/final_publication_benchmark_with_exact_validation.csv`",
        "5. `docs/final_dashboard_demo_script_phase47.md`",
        "6. `docs/final_deployment_checklist_phase47.md`",
    ]

    write_doc(PROFESSOR_PACKET_DOC, lines)


def write_phase47_doc() -> None:
    lines = [
        "# Phase 47 — Final Dashboard, README, Demo, and Deployment Polish",
        "",
        "## Purpose",
        "",
        "Phase 47 completes the prototype package for professor review and final deployment.",
        "",
        "## Generated Files",
        "",
        "- `README.md`",
        "- `docs/final_project_handoff_package.md`",
        "- `docs/final_dashboard_demo_script_phase47.md`",
        "- `docs/final_deployment_checklist_phase47.md`",
        "- `docs/professor_review_packet.md`",
        "- `docs/phase47_final_wrapup_package.md`",
        "- `results/publication_tables/final_project_manifest.csv`",
        "- `results/publication_tables/final_phase_completion_summary.csv`",
        "",
        "## What This Phase Means",
        "",
        "The project is now packaged as a complete prototype and publication-preparation bundle.",
        "",
        "It is ready for professor review, final feedback, and deployment verification.",
        "",
        "## Safe Interpretation",
        "",
        "This is not a final journal submission.",
        "",
        "It is a complete prototype and review package.",
    ]

    write_doc(PHASE47_DOC, lines)


def append_once(path: Path, marker: str, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = ""

    if marker in existing:
        return

    updated = existing.rstrip() + "\n\n" + marker + "\n" + content.strip() + "\n"
    path.write_text(updated, encoding="utf-8")


def update_results_summary() -> None:
    content = """
# Phase 47 Update — Final Wrap-Up Package

Phase 47 completed the final dashboard, README, demo, deployment, and handoff package.

The project now includes a project-local README, final handoff document, professor review packet, final dashboard demo script, deployment checklist, project manifest table, and final phase-completion summary.

Safe interpretation:

The project is complete as a prototype and publication-preparation package for professor review. It is not a final journal submission and does not claim quantum advantage or final biological validation.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE47_MARKER, content)


def update_project_navigation() -> None:
    content = """
# Phase 47 — Final Dashboard, README, Demo, and Deployment Polish

Purpose:

Complete the final prototype package for professor review and deployment.

Main file:

`src/evaluation/phase47_final_wrapup_package.py`

Generated files:

`README.md`  
`docs/final_project_handoff_package.md`  
`docs/final_dashboard_demo_script_phase47.md`  
`docs/final_deployment_checklist_phase47.md`  
`docs/professor_review_packet.md`  
`docs/phase47_final_wrapup_package.md`  
`results/publication_tables/final_project_manifest.csv`  
`results/publication_tables/final_phase_completion_summary.csv`

Run:

`python src\\evaluation\\phase47_final_wrapup_package.py`

Safe interpretation:

Phase 47 completes the prototype and professor-review package. It is not a final journal submission.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE47_MARKER, content)


def main() -> None:
    manifest_rows = build_project_manifest()
    phase_rows = build_phase_completion_summary()

    write_csv(PROJECT_MANIFEST_TABLE, manifest_rows)
    write_csv(PHASE_COMPLETION_TABLE, phase_rows)

    write_project_readme()
    write_final_handoff_doc()
    write_demo_script()
    write_deployment_checklist()
    write_professor_packet()
    write_phase47_doc()

    update_results_summary()
    update_project_navigation()

    print("Phase 47 final wrap-up package complete.")
    print(f"README: {README_PATH}")
    print(f"Final handoff: {FINAL_HANDOFF_DOC}")
    print(f"Demo script: {FINAL_DEMO_SCRIPT_DOC}")
    print(f"Deployment checklist: {FINAL_DEPLOYMENT_DOC}")
    print(f"Professor packet: {PROFESSOR_PACKET_DOC}")
    print(f"Phase 47 documentation: {PHASE47_DOC}")
    print(f"Project manifest: {PROJECT_MANIFEST_TABLE}")
    print(f"Phase completion summary: {PHASE_COMPLETION_TABLE}")


if __name__ == "__main__":
    main()