from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
TABLE_DIR = ROOT / "results" / "publication_tables"

DOCS_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)


LITERATURE_ROWS: List[Dict[str, Any]] = [
    {
        "category": "RNA Folding Foundations",
        "reference_key": "Nussinov Dynamic Programming",
        "method_or_concept": "Classical RNA secondary-structure prediction using dynamic programming.",
        "relevance_to_project": "Supports the reference-pair proxy and classical RNA folding foundation.",
        "gap_for_this_project": "Does not connect RNA folding to QUBO, QAOA, VQE, or qubit compression.",
        "action_needed": "Collect exact citation, DOI, and short summary.",
    },
    {
        "category": "RNA Folding Foundations",
        "reference_key": "Zuker Minimum Free Energy",
        "method_or_concept": "Thermodynamic RNA folding using minimum free energy.",
        "relevance_to_project": "Provides the classical RNA folding baseline direction.",
        "gap_for_this_project": "Not designed as a unified quantum or QUBO benchmark framework.",
        "action_needed": "Collect exact citation and compare against current stem-based QUBO.",
    },
    {
        "category": "RNA Folding Foundations",
        "reference_key": "McCaskill Partition Function",
        "method_or_concept": "Partition function and base-pair probability calculation.",
        "relevance_to_project": "Important for future probabilistic RNA validation.",
        "gap_for_this_project": "Does not directly provide a QUBO-to-quantum benchmark pipeline.",
        "action_needed": "Collect PDF/citation and summarize probability validation use.",
    },
    {
        "category": "RNA Folding Tools",
        "reference_key": "ViennaRNA / RNAfold",
        "method_or_concept": "Practical RNA secondary-structure prediction software.",
        "relevance_to_project": "Main external benchmark target for validating project outputs.",
        "gap_for_this_project": "Powerful classical tool, but not a QUBO/QAOA/VQE/compression benchmark package.",
        "action_needed": "Collect official citation and use as future benchmark comparison.",
    },
    {
        "category": "QUBO Formulation",
        "reference_key": "RNA Folding as QUBO",
        "method_or_concept": "Convert RNA folding into binary optimization.",
        "relevance_to_project": "Directly needed to compare whether our stem-based QUBO is different.",
        "gap_for_this_project": "Need to identify whether prior work reports bioinformatics, quantum, compression, and hardware-readiness metrics together.",
        "action_needed": "Collect at least 3 RNA-QUBO or RNA quantum annealing references.",
    },
    {
        "category": "Classical Optimization",
        "reference_key": "Simulated Annealing",
        "method_or_concept": "Classical probabilistic optimization baseline.",
        "relevance_to_project": "Supports the classical benchmark layer.",
        "gap_for_this_project": "Classical optimization alone does not evaluate quantum feasibility or qubit compression.",
        "action_needed": "Collect simulated annealing and RNA/QUBO benchmark references.",
    },
    {
        "category": "Quantum Optimization",
        "reference_key": "QAOA",
        "method_or_concept": "Parameterized quantum algorithm for combinatorial optimization.",
        "relevance_to_project": "Supports QAOA readiness, circuit prototype, and parameter sweep layers.",
        "gap_for_this_project": "Need to test when QAOA is practical for RNA-QUBO instances.",
        "action_needed": "Collect QAOA references and summarize QUBO-to-circuit mapping.",
    },
    {
        "category": "Quantum Optimization",
        "reference_key": "VQE",
        "method_or_concept": "Hybrid quantum-classical variational optimization.",
        "relevance_to_project": "Supports VQE readiness, circuit prototype, and parameter sweep layers.",
        "gap_for_this_project": "Need to clarify whether VQE is useful for this RNA-QUBO problem class.",
        "action_needed": "Collect VQE references and compare with QAOA feasibility.",
    },
    {
        "category": "Qubit Compression",
        "reference_key": "QRAC",
        "method_or_concept": "Encode multiple classical bits into fewer qubits probabilistically.",
        "relevance_to_project": "Supports the qubit-compression research extension.",
        "gap_for_this_project": "Need to validate whether compressed variables preserve RNA-QUBO solution quality.",
        "action_needed": "Collect QRAC references and identify valid assumptions.",
    },
    {
        "category": "Qubit Compression",
        "reference_key": "QRAO",
        "method_or_concept": "Optimization using QRAC-style compressed variable encoding.",
        "relevance_to_project": "Directly supports the QRAO subset mapping layer.",
        "gap_for_this_project": "Need to test if QRAO-style mapping helps RNA-QUBO while preserving useful bitstrings.",
        "action_needed": "Collect QRAO references and compare direct vs compressed encoding.",
    },
    {
        "category": "Hardware Readiness",
        "reference_key": "NISQ Limitations",
        "method_or_concept": "Current hardware limits: qubits, circuit depth, noise, connectivity, and gate errors.",
        "relevance_to_project": "Supports the hardware-readiness section and no-quantum-advantage limitation.",
        "gap_for_this_project": "Need to define when RNA-QUBO instances are small enough for realistic hardware testing.",
        "action_needed": "Collect NISQ and IBM/Qiskit hardware-readiness references.",
    },
]


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join(["---" for _ in columns]) + " |"
    body = []

    for row in rows:
        body.append("| " + " | ".join(escape_md(row.get(column, "")) for column in columns) + " |")

    return "\n".join([header, divider] + body)


def write_doc(filename: str, lines: List[str]) -> None:
    path = DOCS_DIR / filename
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def create_literature_review_matrix() -> None:
    table = markdown_table(
        LITERATURE_ROWS,
        [
            "category",
            "reference_key",
            "method_or_concept",
            "relevance_to_project",
            "gap_for_this_project",
            "action_needed",
        ],
    )

    write_doc(
        "literature_review_matrix.md",
        [
            "# Literature Review Matrix",
            "",
            "## Purpose",
            "",
            "This matrix organizes the literature review for the RNA-QUBO publication project.",
            "",
            "The goal is to compare the current project against existing work in RNA folding, QUBO formulation, QAOA, VQE, QRAC/QRAO qubit compression, and NISQ hardware-readiness analysis.",
            "",
            "## Important Note",
            "",
            "This is a working literature-review matrix. Exact citations, DOI information, PDF links, and BibTeX entries still need to be collected before manuscript submission.",
            "",
            "## Matrix",
            "",
            table,
            "",
            "## How This Supports the Paper",
            "",
            "This matrix supports the related-work section and helps answer the professor's question:",
            "",
            "**Does this project differ from existing RNA folding and RNA-QUBO formulations?**",
            "",
            "The safe current answer is that the project may be novel as an integrated benchmark framework, but the exact novelty of the QUBO formulation must be verified through literature comparison.",
        ],
    )


def create_research_gap_table() -> None:
    rows = [
        {
            "paper_area": "RNA folding tools",
            "what_existing_work_does": "Predicts RNA secondary structure using classical folding methods.",
            "what_is_missing": "Usually not connected to QUBO, QAOA, VQE, qubit compression, and hardware-readiness in one workflow.",
            "our_project_response": "Adds a path from RNA preprocessing into QUBO and quantum-ready benchmark evaluation.",
        },
        {
            "paper_area": "QUBO RNA folding",
            "what_existing_work_does": "Maps RNA folding into binary optimization using variables and penalties.",
            "what_is_missing": "Often limited to formulation or solver results.",
            "our_project_response": "Adds benchmark tables, classical solvers, quantum feasibility, compression, and hardware-readiness metrics.",
        },
        {
            "paper_area": "Quantum algorithms",
            "what_existing_work_does": "Uses QAOA, VQE, or quantum annealing for optimization.",
            "what_is_missing": "Often does not evaluate RNA-QUBO practicality with sequence length, variables, depth, and hardware readiness together.",
            "our_project_response": "Adds QAOA/VQE readiness, circuit-depth estimates, energy proxies, bitstrings, and hardware-readiness labels.",
        },
        {
            "paper_area": "Qubit compression",
            "what_existing_work_does": "Studies QRAC/QRAO-style compression for optimization.",
            "what_is_missing": "RNA-QUBO-specific compression quality is not yet established.",
            "our_project_response": "Adds direct vs compressed qubit estimates and QRAO-style mapping as a research extension.",
        },
    ]

    table = markdown_table(
        rows,
        [
            "paper_area",
            "what_existing_work_does",
            "what_is_missing",
            "our_project_response",
        ],
    )

    write_doc(
        "research_gap_table.md",
        [
            "# Research Gap Table",
            "",
            "## Main Research Gap",
            "",
            "The main research gap is the lack of a unified, reproducible benchmark workflow that connects RNA sequence preprocessing, QUBO formulation, classical optimization, QAOA/VQE feasibility, qubit compression, hardware readiness, and publication-ready benchmark tables.",
            "",
            "The project should not claim quantum advantage.",
            "",
            "The strongest contribution is the integrated benchmark framework.",
            "",
            "## Gap Table",
            "",
            table,
            "",
            "## Draft Research Gap Statement",
            "",
            "Existing RNA secondary-structure prediction tools are strong classical methods, and existing QUBO or quantum optimization studies explore important pieces of the problem. However, many approaches focus on a single layer: RNA folding, QUBO formulation, quantum solver testing, or hardware feasibility.",
            "",
            "This project addresses that gap by creating an integrated bioinformatics-to-quantum benchmark workflow.",
        ],
    )


def create_qubo_formulation_comparison() -> None:
    rows = [
        {
            "comparison_item": "Decision variable",
            "traditional_rna_folding": "Base-pair or structural decisions.",
            "existing_rna_qubo_to_compare": "May use base-pair variables, stem variables, or other binary encodings.",
            "current_project": "Candidate stems are represented as binary variables.",
            "evidence_needed": "Compare variable definitions across RNA-QUBO papers.",
        },
        {
            "comparison_item": "Objective function",
            "traditional_rna_folding": "Minimizes free energy or maximizes structural score.",
            "existing_rna_qubo_to_compare": "Uses QUBO weights based on base-pair or stem scoring.",
            "current_project": "Uses simplified stem score as a linear reward.",
            "evidence_needed": "Compare scoring with prior thermodynamic models.",
        },
        {
            "comparison_item": "Penalty constraints",
            "traditional_rna_folding": "Constraints handled through recursion or energy rules.",
            "existing_rna_qubo_to_compare": "Uses penalties for overlap, conflict, crossing, or invalid structures.",
            "current_project": "Adds quadratic penalties for overlapping or crossing candidate stems.",
            "evidence_needed": "Compare exact penalty types and penalty strengths.",
        },
        {
            "comparison_item": "Qubit compression",
            "traditional_rna_folding": "Not applicable.",
            "existing_rna_qubo_to_compare": "May not include QRAC/QRAO compression.",
            "current_project": "Adds direct vs 2-to-1 and 3-to-1 compression estimates.",
            "evidence_needed": "Verify whether RNA-QUBO papers include compression.",
        },
    ]

    table = markdown_table(
        rows,
        [
            "comparison_item",
            "traditional_rna_folding",
            "existing_rna_qubo_to_compare",
            "current_project",
            "evidence_needed",
        ],
    )

    write_doc(
        "qubo_formulation_comparison.md",
        [
            "# QUBO Formulation Comparison",
            "",
            "## Purpose",
            "",
            "This document organizes how the current QUBO formulation should be compared against existing RNA folding and RNA-QUBO formulations.",
            "",
            "The professor's key question is:",
            "",
            "**Does your QUBO formulation differ from existing RNA folding formulations?**",
            "",
            "The answer must be evidence-based. We should not claim formulation novelty until related papers are reviewed carefully.",
            "",
            "## Current Project Formulation",
            "",
            "The current project uses a prototype stem-based QUBO model.",
            "",
            "- RNA sequence is cleaned into valid A/U/G/C bases.",
            "- Candidate base pairs are generated from Watson-Crick and wobble pair rules.",
            "- Candidate stems are built from compatible pairs.",
            "- Each candidate stem becomes a binary decision variable.",
            "- Linear QUBO terms reward stronger candidate stems.",
            "- Quadratic QUBO terms penalize incompatible stems.",
            "- The benchmark records variables, linear terms, quadratic terms, and QUBO density.",
            "",
            "## Comparison Table",
            "",
            table,
            "",
            "## Careful Novelty Position",
            "",
            "This project contributes a stem-based RNA-QUBO prototype within a larger integrated benchmark framework. The exact novelty of the QUBO formulation must be verified by comparing variable definitions, constraints, penalty terms, scaling behavior, and solver pathways against existing RNA-QUBO and RNA quantum annealing literature.",
        ],
    )


def create_publication_references_to_collect() -> None:
    write_doc(
        "publication_references_to_collect.md",
        [
            "# Publication References to Collect",
            "",
            "## Purpose",
            "",
            "This document lists the reference groups needed before writing the final paper draft.",
            "",
            "## Required Reference Groups",
            "",
            "### 1. RNA Folding Foundations",
            "",
            "- Nussinov dynamic programming RNA folding",
            "- Zuker minimum free energy RNA folding",
            "- McCaskill partition function and base-pair probabilities",
            "- RNA secondary-structure prediction surveys",
            "",
            "### 2. ViennaRNA / RNAfold",
            "",
            "- ViennaRNA Package citation",
            "- RNAfold manual or official documentation",
            "- Benchmark or usage references",
            "",
            "### 3. RNA QUBO / Quantum Annealing",
            "",
            "- RNA folding as QUBO",
            "- RNA folding as Ising model",
            "- RNA secondary-structure prediction using quantum annealing",
            "- RNA optimization on D-Wave or other annealers",
            "",
            "### 4. QAOA and VQE",
            "",
            "- Original QAOA paper",
            "- Original VQE paper",
            "- QAOA for combinatorial optimization references",
            "- VQE or variational algorithm references for optimization",
            "",
            "### 5. QRAC / QRAO Qubit Compression",
            "",
            "- Quantum Random Access Code references",
            "- Quantum Random Access Optimization references",
            "- Qubit-efficient encoding for combinatorial optimization",
            "- Pauli X/Y/Z variable mapping references",
            "",
            "### 6. Hardware Readiness and NISQ Limits",
            "",
            "- NISQ limitations",
            "- Circuit depth limitations",
            "- Qubit count limitations",
            "- Noise and error rates",
            "- IBM Quantum / Qiskit hardware constraints",
            "",
            "## Minimum Reference Goal",
            "",
            "- 3 RNA folding foundation references",
            "- 1 ViennaRNA/RNAfold official reference",
            "- 3 RNA-QUBO or RNA quantum annealing references",
            "- 2 QAOA/VQE references",
            "- 2 QRAC/QRAO references",
            "- 2 NISQ hardware-readiness references",
            "",
            "Minimum total target: **13-15 strong references**",
            "",
            "## Important Rule",
            "",
            "Do not claim that the QUBO formulation is new until the existing RNA-QUBO literature is reviewed.",
            "",
            "The safest current novelty claim is:",
            "",
            "**The project contributes an integrated bioinformatics-to-quantum benchmark framework that combines RNA preprocessing, QUBO formulation, classical optimization, QAOA/VQE feasibility, qubit-compression analysis, and hardware-readiness reporting.**",
        ],
    )


def main() -> None:
    write_csv(TABLE_DIR / "literature_review_matrix.csv", LITERATURE_ROWS)

    create_literature_review_matrix()
    create_research_gap_table()
    create_qubo_formulation_comparison()
    create_publication_references_to_collect()

    print("Phase 39 literature review package complete.")
    print(f"CSV written to: {TABLE_DIR / 'literature_review_matrix.csv'}")
    print("Docs created:")
    print("- docs/literature_review_matrix.md")
    print("- docs/research_gap_table.md")
    print("- docs/qubo_formulation_comparison.md")
    print("- docs/publication_references_to_collect.md")


if __name__ == "__main__":
    main()