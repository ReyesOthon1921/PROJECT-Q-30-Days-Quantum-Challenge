from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]

DOCS_DIR = ROOT / "docs"
MANUSCRIPT_DIR = DOCS_DIR / "manuscript"
TABLE_DIR = ROOT / "results" / "publication_tables"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
MANUSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

FINAL_BENCHMARK = TABLE_DIR / "final_publication_benchmark_with_exact_validation.csv"
EXACT_SUMMARY = TABLE_DIR / "exact_validation_integrated_summary.csv"
QRAO_SUMMARY = TABLE_DIR / "graph_aware_qrao_summary.csv"
DATASET_READINESS = TABLE_DIR / "phase45_dataset_readiness_summary.csv"
LITERATURE_MATRIX = TABLE_DIR / "literature_review_matrix.csv"
ENERGY_AUDIT_SUMMARY = TABLE_DIR / "qubo_energy_audit_summary.csv"
QUBO_ISING = TABLE_DIR / "qubo_to_ising_coefficients.csv"

KEY_RESULTS_TABLE = TABLE_DIR / "manuscript_key_results_summary.csv"
SECTION_SOURCE_MAP = TABLE_DIR / "manuscript_section_source_map.csv"

ABSTRACT_DOC = MANUSCRIPT_DIR / "abstract.md"
INTRODUCTION_DOC = MANUSCRIPT_DIR / "introduction.md"
RELATED_WORK_DOC = MANUSCRIPT_DIR / "related_work.md"
METHODOLOGY_DOC = MANUSCRIPT_DIR / "methodology.md"
RESULTS_DOC = MANUSCRIPT_DIR / "results.md"
DISCUSSION_DOC = MANUSCRIPT_DIR / "discussion.md"
LIMITATIONS_DOC = MANUSCRIPT_DIR / "limitations.md"
CONCLUSION_DOC = MANUSCRIPT_DIR / "conclusion.md"
FUTURE_WORK_DOC = MANUSCRIPT_DIR / "future_work.md"
FULL_MANUSCRIPT_DOC = MANUSCRIPT_DIR / "full_manuscript_draft.md"

PHASE46_DOC = DOCS_DIR / "phase46_manuscript_assembly_package.md"
RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"

PHASE46_MARKER = "<!-- PHASE46_MANUSCRIPT_ASSEMBLY_PACKAGE -->"


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


def safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except ValueError:
        return None


def safe_int(value: Any) -> Optional[int]:
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(float(value))
    except ValueError:
        return None


def summary_value(rows: List[Dict[str, str]], item_name: str, default: str = "not available") -> str:
    for row in rows:
        if row.get("summary_item") == item_name:
            return str(row.get("value", default))

    return default


def min_float(rows: List[Dict[str, str]], key: str) -> str:
    values = [safe_float(row.get(key)) for row in rows]
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return "not available"

    return str(min(clean_values))


def max_float(rows: List[Dict[str, str]], key: str) -> str:
    values = [safe_float(row.get(key)) for row in rows]
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return "not available"

    return str(max(clean_values))


def sum_int(rows: List[Dict[str, str]], key: str) -> int:
    values = [safe_int(row.get(key)) for row in rows]
    return sum(value for value in values if value is not None)


def build_key_results() -> List[Dict[str, Any]]:
    final_rows = read_csv(FINAL_BENCHMARK)
    exact_rows = read_csv(EXACT_SUMMARY)
    qrao_rows = read_csv(QRAO_SUMMARY)
    dataset_rows = read_csv(DATASET_READINESS)
    literature_rows = read_csv(LITERATURE_MATRIX)
    energy_rows = read_csv(ENERGY_AUDIT_SUMMARY)
    ising_rows = read_csv(QUBO_ISING)

    qrao_pass_count = sum(1 for row in qrao_rows if row.get("validation_status") == "pass")

    exact_feasible_count = sum(
        1 for row in exact_rows
        if str(row.get("feasible", "")).lower() == "true"
    )

    rows = [
        {
            "metric": "final_benchmark_rows",
            "value": len(final_rows),
            "source": str(FINAL_BENCHMARK),
            "interpretation": "Rows available in the integrated final benchmark table.",
        },
        {
            "metric": "dataset_sequences_tracked",
            "value": summary_value(dataset_rows, "total_sequences"),
            "source": str(DATASET_READINESS),
            "interpretation": "RNA sequences tracked for exact validation or external validation planning.",
        },
        {
            "metric": "exact_validation_sequences",
            "value": len(exact_rows),
            "source": str(EXACT_SUMMARY),
            "interpretation": "Small RNA-QUBO instances with exact validation summaries.",
        },
        {
            "metric": "exact_feasible_optima",
            "value": exact_feasible_count,
            "source": str(EXACT_SUMMARY),
            "interpretation": "Exact optima reported as feasible under current hard constraints.",
        },
        {
            "metric": "total_exact_assignments_checked",
            "value": sum_int(exact_rows, "assignment_count"),
            "source": str(EXACT_SUMMARY),
            "interpretation": "Total bitstring assignments checked by exact enumeration.",
        },
        {
            "metric": "best_exact_minimum_energy",
            "value": min_float(exact_rows, "exact_minimum_energy"),
            "source": str(EXACT_SUMMARY),
            "interpretation": "Lowest exact QUBO energy among exact-validation instances.",
        },
        {
            "metric": "worst_exact_minimum_energy",
            "value": max_float(exact_rows, "exact_minimum_energy"),
            "source": str(EXACT_SUMMARY),
            "interpretation": "Highest exact QUBO optimum energy among exact-validation instances.",
        },
        {
            "metric": "energy_audit_sequences",
            "value": len(energy_rows),
            "source": str(ENERGY_AUDIT_SUMMARY),
            "interpretation": "Sequences with term-by-term energy audit summaries.",
        },
        {
            "metric": "qubo_to_ising_coefficient_rows",
            "value": len(ising_rows),
            "source": str(QUBO_ISING),
            "interpretation": "Rows exported for QUBO-to-Ising coefficient interpretation.",
        },
        {
            "metric": "graph_aware_qrao_sequences",
            "value": len(qrao_rows),
            "source": str(QRAO_SUMMARY),
            "interpretation": "Sequences analyzed with graph-aware QRAO compression logic.",
        },
        {
            "metric": "graph_aware_qrao_pass_count",
            "value": qrao_pass_count,
            "source": str(QRAO_SUMMARY),
            "interpretation": "Graph-aware QRAO rows passing no-same-qubit conflict checks.",
        },
        {
            "metric": "literature_review_entries",
            "value": len(literature_rows),
            "source": str(LITERATURE_MATRIX),
            "interpretation": "Rows available in the literature review matrix.",
        },
    ]

    return rows


def value_from_key_results(key_rows: List[Dict[str, Any]], metric: str) -> str:
    for row in key_rows:
        if row["metric"] == metric:
            return str(row["value"])

    return "not available"


def write_manuscript_sections(key_rows: List[Dict[str, Any]]) -> None:
    dataset_sequences = value_from_key_results(key_rows, "dataset_sequences_tracked")
    exact_sequences = value_from_key_results(key_rows, "exact_validation_sequences")
    exact_assignments = value_from_key_results(key_rows, "total_exact_assignments_checked")
    best_energy = value_from_key_results(key_rows, "best_exact_minimum_energy")
    qrao_sequences = value_from_key_results(key_rows, "graph_aware_qrao_sequences")
    qrao_pass_count = value_from_key_results(key_rows, "graph_aware_qrao_pass_count")
    literature_entries = value_from_key_results(key_rows, "literature_review_entries")

    write_doc(
        ABSTRACT_DOC,
        [
            "# Abstract",
            "",
            "RNA secondary-structure prediction can be framed as an optimization problem, which makes it a candidate for QUBO modeling and quantum-optimization exploration.",
            "",
            "This project presents a prototype bioinformatics-to-quantum benchmarking framework for RNA secondary-structure optimization using candidate stem generation, stem-based QUBO construction, classical solvers, QAOA/VQE feasibility modules, exact small-instance validation, QUBO-to-Ising conversion, and qubit-compression analysis.",
            "",
            f"The current validation package tracks {dataset_sequences} RNA sequences, includes {exact_sequences} exact-validation instances, and checks {exact_assignments} total bitstring assignments by exact enumeration.",
            "",
            f"The best exact minimum QUBO energy currently observed across the exact-validation set is {best_energy}.",
            "",
            "The project also adds graph-aware QRAO compression validation to test whether QUBO interaction-graph structure can guide safer variable packing.",
            "",
            "This work does not claim quantum advantage, clinical accuracy, or final biological validation. Its contribution is an integrated, auditable research framework that connects RNA preprocessing, QUBO modeling, exact validation, quantum feasibility analysis, compression analysis, and publication-ready documentation.",
        ],
    )

    write_doc(
        INTRODUCTION_DOC,
        [
            "# 1. Introduction",
            "",
            "RNA molecules can fold into secondary structures that influence biological function. Predicting these structures is a central task in computational biology.",
            "",
            "Traditional RNA secondary-structure prediction methods often rely on dynamic programming, thermodynamic scoring, and minimum free energy modeling. Quantum and quantum-inspired approaches require a different representation: the biological problem must be translated into an optimization model such as QUBO or Ising form.",
            "",
            "This project explores that bridge. It builds a workflow that starts with RNA sequence preprocessing, generates candidate pairs and stems, formulates a stem-based QUBO, validates small instances exactly, and connects the resulting model to classical solvers, QAOA/VQE feasibility modules, and qubit-compression analysis.",
            "",
            "The project is motivated by the need for careful, auditable benchmarking. Before quantum or compression results can be interpreted responsibly, the QUBO model must be traceable from sequence to variables, coefficients, assumptions, exact optima, decoded structures, and benchmark outputs.",
            "",
            "The main research question is:",
            "",
            "**Can RNA secondary-structure prediction be represented as a QUBO problem and evaluated through a unified classical, quantum, exact-validation, and qubit-compression benchmarking framework?**",
        ],
    )

    write_doc(
        RELATED_WORK_DOC,
        [
            "# 2. Related Work",
            "",
            "The project connects several research areas:",
            "",
            "## RNA Folding",
            "",
            "The RNA side includes secondary-structure prediction, base-pairing rules, dot-bracket notation, minimum free energy methods, Nussinov-style dynamic programming, Zuker-style approaches, McCaskill partition functions, and ViennaRNA/RNAfold-style validation.",
            "",
            "## QUBO and Ising Formulations",
            "",
            "The optimization side includes binary decision variables, objective functions, penalty constraints, Hamiltonian construction, QUBO matrix conventions, and QUBO-to-Ising mappings.",
            "",
            "## Quantum Algorithms",
            "",
            "The quantum side includes QAOA, VQE, quantum annealing, parameter sweeps, measured bitstrings, hardware-readiness estimates, and NISQ-era limitations.",
            "",
            "## Qubit Compression",
            "",
            "The compression side includes direct one-variable-per-qubit encoding, QRAC, QRAO, variable grouping, Pauli X/Y/Z assignment, rounding, and interaction-graph-aware packing.",
            "",
            f"The current literature review matrix contains {literature_entries} tracked entries or placeholders. These references must be expanded and verified before final journal submission.",
        ],
    )

    write_doc(
        METHODOLOGY_DOC,
        [
            "# 3. Methodology",
            "",
            "The methodology follows an end-to-end research pipeline:",
            "",
            "`RNA sequence -> preprocessing -> candidate pairs -> candidate stems -> stem-QUBO formulation -> exact validation -> classical benchmark -> quantum feasibility -> qubit compression -> hardware readiness -> publication outputs`",
            "",
            "## 3.1 RNA Preprocessing",
            "",
            "Input sequences are cleaned and represented using the RNA alphabet A, U, G, and C. Sequence length, GC content, AU content, candidate-pair count, and candidate-stem count are recorded.",
            "",
            "## 3.2 Candidate Pair and Stem Generation",
            "",
            "Candidate base pairs are generated using Watson-Crick and wobble-pair rules. Candidate stems are then constructed from compatible stacked or grouped base-pair candidates.",
            "",
            "## 3.3 Stem-Based QUBO Formulation",
            "",
            "Each candidate stem is represented as a binary variable. Favorable stems receive negative linear energy, while incompatible stem selections receive quadratic penalties for overlap or forbidden crossing patterns.",
            "",
            "## 3.4 Exact Validation",
            "",
            "For small QUBO instances, all bitstrings are enumerated to identify exact minimum energy, degenerate minima, feasibility, decoded pairs, dot-bracket output, and energy decomposition.",
            "",
            "## 3.5 QUBO-to-Ising Conversion",
            "",
            "The QUBO is converted into Ising-style coefficients to support cost-Hamiltonian interpretation for QAOA and VQE-style modules.",
            "",
            "## 3.6 Classical and Quantum Benchmarking",
            "",
            "Classical benchmarking uses greedy and simulated annealing baselines. Quantum modules include QAOA readiness, VQE readiness, circuit prototypes, parameter sweeps, measured bitstring energy, and hardware-readiness checks.",
            "",
            "## 3.7 Graph-Aware QRAO Compression",
            "",
            "The QUBO interaction graph is used to guide compression. Interacting variables are not assigned to the same compressed qubit under the graph-aware QRAO packing logic.",
            "",
            "## 3.8 External Validation Planning",
            "",
            "RNAfold/ViennaRNA, BLAST, and RCSB PDB are planned as external validation/context layers. These outputs must be manually executed and verified before being treated as evidence.",
        ],
    )

    write_doc(
        RESULTS_DOC,
        [
            "# 4. Results",
            "",
            "The project currently produces tables, figures, documentation, and a live dashboard supporting the RNA-QUBO workflow.",
            "",
            "## 4.1 Dataset Readiness",
            "",
            f"The current validation dataset tracks {dataset_sequences} RNA sequences across exact-validation and bioinformatics-expansion groups.",
            "",
            "## 4.2 Exact Validation",
            "",
            f"The exact-validation layer currently includes {exact_sequences} small RNA-QUBO instances.",
            "",
            f"Across these instances, exact enumeration checked {exact_assignments} total bitstring assignments.",
            "",
            f"The best exact minimum QUBO energy observed is {best_energy}.",
            "",
            "The exact-validation tables include exact minimum energy, degenerate minima count, best bitstring, feasibility, decoded base pairs, dot-bracket output, and energy audit terms.",
            "",
            "## 4.3 Energy Audit",
            "",
            "The QUBO energy audit separates the exact optimum into linear stem rewards, overlap penalties, crossing penalties, compatible interaction terms, and total energy.",
            "",
            "## 4.4 QUBO-to-Ising Mapping",
            "",
            "The project exports QUBO-to-Ising coefficients, including constant offsets, linear fields, and pairwise couplings.",
            "",
            "## 4.5 Graph-Aware QRAO Compression",
            "",
            f"The graph-aware QRAO validation layer analyzes {qrao_sequences} exact-validation sequences.",
            "",
            f"{qrao_pass_count} graph-aware QRAO rows currently pass the no-same-qubit conflict check.",
            "",
            "This confirms the mapping logic avoids assigning interacting QUBO variables to the same compressed qubit under the tested packing rule.",
            "",
            "## 4.6 Figures",
            "",
            "The current figure package includes scaling plots, quantum benchmark plots, exact-validation figures, and graph-aware QRAO figures.",
        ],
    )

    write_doc(
        DISCUSSION_DOC,
        [
            "# 5. Discussion",
            "",
            "The project has moved beyond a simple dashboard into an auditable research workflow.",
            "",
            "The most important progress is the addition of exact small-instance validation. This gives the project a ground-truth layer for small QUBO instances before interpreting heuristic, quantum, or compression outputs.",
            "",
            "The graph-aware QRAO phase also strengthens the compression direction. Instead of only estimating qubit savings by dividing variables into smaller counts, the project now uses the QUBO interaction graph to avoid placing interacting variables on the same compressed qubit.",
            "",
            "This is important because compression should not be treated as a simple variable-count reduction. It must be evaluated as a relaxation that requires mapping, rounding, feasibility checks, and comparison against exact or best-known solutions.",
            "",
            "The biological validation side is still being expanded. Phase 45 added dataset tracking and external-validation planning, but RNAfold/ViennaRNA, BLAST, and RCSB results still need to be manually collected and verified before biological claims are made.",
        ],
    )

    write_doc(
        LIMITATIONS_DOC,
        [
            "# 6. Limitations",
            "",
            "This project is a prototype benchmark and feasibility framework.",
            "",
            "The project does not claim:",
            "",
            "- quantum advantage,",
            "- clinical accuracy,",
            "- production RNA design readiness,",
            "- final biological validation,",
            "- proven QUBO novelty before literature comparison,",
            "- proven compression improvement before rounded-solution validation.",
            "",
            "Exact enumeration is only practical for small QUBO instances because the number of assignments grows exponentially.",
            "",
            "The current energy model is simplified and does not fully replace thermodynamic RNA folding models.",
            "",
            "The QAOA and VQE layers are feasibility/proxy layers and should not be interpreted as evidence of quantum advantage.",
            "",
            "The graph-aware QRAO layer validates mapping logic, but future work must test rounded compressed solutions against exact optima and biological reference structures.",
            "",
            "The RNAfold, BLAST, and RCSB validation plans are not complete until the external outputs are collected and recorded.",
        ],
    )

    write_doc(
        CONCLUSION_DOC,
        [
            "# 7. Conclusion",
            "",
            "This project demonstrates an end-to-end RNA secondary-structure optimization research workflow that connects bioinformatics preprocessing, stem-based QUBO formulation, exact validation, classical benchmarking, QAOA/VQE feasibility analysis, QUBO-to-Ising conversion, graph-aware QRAO compression, hardware-readiness evaluation, and publication-ready documentation.",
            "",
            "The strongest current contribution is not a claim of quantum advantage. The strongest contribution is the integrated and auditable framework.",
            "",
            "The project now provides a structured way to trace RNA sequence inputs into QUBO variables, coefficients, exact optima, energy audits, quantum-feasibility outputs, compression mappings, and manuscript-ready results.",
        ],
    )

    write_doc(
        FUTURE_WORK_DOC,
        [
            "# 8. Future Work",
            "",
            "Future work should focus on:",
            "",
            "1. Expanding the RNA dataset with verified biological references.",
            "2. Running and recording RNAfold/ViennaRNA outputs.",
            "3. Adding reference dot-bracket structures and MFE values.",
            "4. Comparing QUBO predictions against RNAfold base-pair sets.",
            "5. Testing rounded QRAO compressed solutions against exact optima.",
            "6. Adding noise simulation and hardware-aware circuit constraints.",
            "7. Expanding the literature review with verified citations.",
            "8. Preparing the manuscript for professor review and possible journal formatting.",
            "",
            "The next project phase should focus on final demo packaging, README cleanup, deployment verification, and professor-review readiness.",
        ],
    )


def assemble_full_manuscript() -> None:
    sections = [
        ABSTRACT_DOC,
        INTRODUCTION_DOC,
        RELATED_WORK_DOC,
        METHODOLOGY_DOC,
        RESULTS_DOC,
        DISCUSSION_DOC,
        LIMITATIONS_DOC,
        CONCLUSION_DOC,
        FUTURE_WORK_DOC,
    ]

    lines = [
        "# Full Manuscript Draft",
        "",
        "**Working Title:** A Bioinformatics-to-Quantum Benchmarking Framework for RNA Secondary Structure Prediction Using QUBO, QAOA, VQE, and Qubit-Compression Analysis",
        "",
        "**Status:** Draft manuscript package for professor review. This is not a final journal submission.",
        "",
        "---",
        "",
    ]

    for section in sections:
        if section.exists():
            lines.append(section.read_text(encoding="utf-8").strip())
            lines.append("")
            lines.append("---")
            lines.append("")

    write_doc(FULL_MANUSCRIPT_DOC, lines)


def build_source_map() -> List[Dict[str, Any]]:
    return [
        {
            "manuscript_section": "Abstract",
            "generated_file": str(ABSTRACT_DOC),
            "main_sources": "final benchmark, exact validation summary, graph-aware QRAO summary",
        },
        {
            "manuscript_section": "Introduction",
            "generated_file": str(INTRODUCTION_DOC),
            "main_sources": "research problem, project roadmap, methodology notes",
        },
        {
            "manuscript_section": "Related Work",
            "generated_file": str(RELATED_WORK_DOC),
            "main_sources": "literature review matrix, reference collection checklist",
        },
        {
            "manuscript_section": "Methodology",
            "generated_file": str(METHODOLOGY_DOC),
            "main_sources": "mathematical formulation, exact validation protocol, QUBO documentation",
        },
        {
            "manuscript_section": "Results",
            "generated_file": str(RESULTS_DOC),
            "main_sources": "publication tables, exact validation, energy audit, QRAO tables",
        },
        {
            "manuscript_section": "Discussion",
            "generated_file": str(DISCUSSION_DOC),
            "main_sources": "limitations, validation notes, compression notes",
        },
        {
            "manuscript_section": "Limitations",
            "generated_file": str(LIMITATIONS_DOC),
            "main_sources": "limitations document, safe claim boundaries",
        },
        {
            "manuscript_section": "Conclusion",
            "generated_file": str(CONCLUSION_DOC),
            "main_sources": "final project summary, benchmark workflow",
        },
        {
            "manuscript_section": "Future Work",
            "generated_file": str(FUTURE_WORK_DOC),
            "main_sources": "dataset validation plan, external validation plan, professor roadmap",
        },
        {
            "manuscript_section": "Full Draft",
            "generated_file": str(FULL_MANUSCRIPT_DOC),
            "main_sources": "all generated manuscript sections",
        },
    ]


def write_phase46_doc(key_rows: List[Dict[str, Any]]) -> None:
    manuscript_files = [
        ABSTRACT_DOC,
        INTRODUCTION_DOC,
        RELATED_WORK_DOC,
        METHODOLOGY_DOC,
        RESULTS_DOC,
        DISCUSSION_DOC,
        LIMITATIONS_DOC,
        CONCLUSION_DOC,
        FUTURE_WORK_DOC,
        FULL_MANUSCRIPT_DOC,
    ]

    lines = [
        "# Phase 46 — Manuscript Assembly Package",
        "",
        "## Purpose",
        "",
        "Phase 46 assembles the current research outputs into a paper-style manuscript draft.",
        "",
        "This phase does not create a final journal submission. It creates a structured draft package for professor review.",
        "",
        "## Generated Manuscript Files",
        "",
    ]

    for file_path in manuscript_files:
        lines.append(f"- `{file_path.relative_to(ROOT)}`")

    lines.extend(
        [
            "",
            "## Generated Tables",
            "",
            "- `results/publication_tables/manuscript_key_results_summary.csv`",
            "- `results/publication_tables/manuscript_section_source_map.csv`",
            "",
            "## Key Result Metrics Used",
            "",
        ]
    )

    for row in key_rows:
        lines.append(f"- `{row['metric']}`: {row['value']}")

    lines.extend(
        [
            "",
            "## Safe Interpretation",
            "",
            "This manuscript package summarizes the current prototype benchmark and feasibility framework.",
            "",
            "It does not claim quantum advantage, clinical accuracy, final biological validation, or completed external validation.",
            "",
            "The package is intended for professor review, revision, and future manuscript development.",
        ]
    )

    write_doc(PHASE46_DOC, lines)


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
# Phase 46 Update — Manuscript Assembly Package

Phase 46 assembled the current research outputs into a paper-style manuscript draft.

Generated sections include abstract, introduction, related work, methodology, results, discussion, limitations, conclusion, future work, and a full manuscript draft.

This package is intended for professor review and future paper development. It is not a final journal submission.

Safe interpretation:

The manuscript describes a prototype benchmark and feasibility framework. It does not claim quantum advantage, clinical accuracy, or final biological validation.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE46_MARKER, content)


def update_project_navigation() -> None:
    content = """
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

`python src\\evaluation\\phase46_manuscript_assembly_package.py`

Safe interpretation:

Phase 46 creates a professor-review manuscript draft package. It is not a final journal submission.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE46_MARKER, content)


def main() -> None:
    key_rows = build_key_results()
    source_map_rows = build_source_map()

    write_csv(KEY_RESULTS_TABLE, key_rows)
    write_csv(SECTION_SOURCE_MAP, source_map_rows)

    write_manuscript_sections(key_rows)
    assemble_full_manuscript()
    write_phase46_doc(key_rows)

    update_results_summary()
    update_project_navigation()

    print("Phase 46 manuscript assembly package complete.")
    print(f"Full manuscript draft: {FULL_MANUSCRIPT_DOC}")
    print(f"Manuscript folder: {MANUSCRIPT_DIR}")
    print(f"Phase 46 documentation: {PHASE46_DOC}")
    print(f"Key results table: {KEY_RESULTS_TABLE}")
    print(f"Section source map: {SECTION_SOURCE_MAP}")


if __name__ == "__main__":
    main()