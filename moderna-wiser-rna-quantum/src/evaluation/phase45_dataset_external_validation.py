from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = ROOT / "data"
TABLE_DIR = ROOT / "results" / "publication_tables"
FIGURE_DIR = ROOT / "results" / "publication_figures"
DOCS_DIR = ROOT / "docs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DATASET_TABLE = DATA_DIR / "rna_validation_dataset.csv"
DATASET_TRACKER_TABLE = TABLE_DIR / "external_validation_dataset_tracker.csv"
RNAFOLD_PLAN_TABLE = TABLE_DIR / "rnafold_validation_plan.csv"
BLAST_RCSB_PLAN_TABLE = TABLE_DIR / "blast_rcsb_reference_plan.csv"
READINESS_SUMMARY_TABLE = TABLE_DIR / "phase45_dataset_readiness_summary.csv"

SEQUENCE_LENGTH_FIGURE = FIGURE_DIR / "dataset_sequence_lengths.png"
GC_CONTENT_FIGURE = FIGURE_DIR / "dataset_gc_content.png"

PHASE45_DOC = DOCS_DIR / "phase45_dataset_external_validation.md"
RESULTS_SUMMARY_DOC = DOCS_DIR / "results_summary.md"
PROJECT_NAVIGATION_DOC = DOCS_DIR / "project_navigation_guide.md"

PHASE45_MARKER = "<!-- PHASE45_DATASET_EXTERNAL_VALIDATION -->"

PAIR_RULES = {
    ("A", "U"),
    ("U", "A"),
    ("G", "C"),
    ("C", "G"),
    ("G", "U"),
    ("U", "G"),
}

DATASET = [
    {
        "sequence_id": "EXACT_01_short_hairpin",
        "sequence": "GGGAAAUCC",
        "dataset_group": "exact_validation_control",
        "source_type": "controlled_demo",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "Small controlled instance already used for exact QUBO validation.",
    },
    {
        "sequence_id": "EXACT_02_balanced_short",
        "sequence": "AUGCUAGCUA",
        "dataset_group": "exact_validation_control",
        "source_type": "controlled_demo",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "Balanced short RNA instance used for exact QUBO audit.",
    },
    {
        "sequence_id": "EXACT_03_gc_rich",
        "sequence": "GCGCGAUUCGC",
        "dataset_group": "exact_validation_control",
        "source_type": "controlled_demo",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "GC-rich controlled instance for coefficient and conflict checking.",
    },
    {
        "sequence_id": "EXACT_04_demo_subset",
        "sequence": "GGCGCAAAACUUGUCGAAU",
        "dataset_group": "exact_validation_control",
        "source_type": "controlled_demo",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "Truncated demo-style sequence used for exact validation.",
    },
    {
        "sequence_id": "BIO_01_short_synthetic",
        "sequence": "GGGCUUAAAGCC",
        "dataset_group": "bioinformatics_expansion",
        "source_type": "synthetic_rna",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "Short synthetic RNA-like sequence for future RNAfold comparison.",
    },
    {
        "sequence_id": "BIO_02_medium_synthetic",
        "sequence": "AUGGCCAUUGUAAUGGGCCGCUGAAAGGGUGCCCGA",
        "dataset_group": "bioinformatics_expansion",
        "source_type": "synthetic_rna",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "Medium synthetic RNA-like sequence for scaling and validation planning.",
    },
    {
        "sequence_id": "BIO_03_gc_balanced",
        "sequence": "GCAUCGGAUUACGCGAAUUCGAUCGC",
        "dataset_group": "bioinformatics_expansion",
        "source_type": "synthetic_rna",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "GC-balanced RNA-like sequence for candidate-pair/stem analysis.",
    },
    {
        "sequence_id": "BIO_04_au_rich",
        "sequence": "AUAUAUGGAAUUCCAAUAUAUGGCUA",
        "dataset_group": "bioinformatics_expansion",
        "source_type": "synthetic_rna",
        "reference_status": "needs_rnafold_reference",
        "external_validation_status": "planned",
        "notes": "AU-rich RNA-like sequence for checking pair diversity.",
    },
]


def clean_sequence(sequence: str) -> str:
    sequence = sequence.upper().replace("T", "U")
    return "".join(base for base in sequence if base in {"A", "U", "G", "C"})


def gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0

    gc_count = sequence.count("G") + sequence.count("C")
    return round(100.0 * gc_count / len(sequence), 3)


def au_content(sequence: str) -> float:
    if not sequence:
        return 0.0

    au_count = sequence.count("A") + sequence.count("U")
    return round(100.0 * au_count / len(sequence), 3)


def can_pair(left: str, right: str) -> bool:
    return (left, right) in PAIR_RULES


def candidate_pairs(sequence: str, min_loop: int = 3) -> List[tuple[int, int]]:
    pairs: List[tuple[int, int]] = []

    for i in range(len(sequence)):
        for j in range(i + min_loop + 1, len(sequence)):
            if can_pair(sequence[i], sequence[j]):
                pairs.append((i, j))

    return pairs


def candidate_stems(sequence: str, max_stem_length: int = 3) -> List[tuple[tuple[int, int], ...]]:
    pair_set = set(candidate_pairs(sequence))
    stems = set()

    for i, j in sorted(pair_set):
        current: List[tuple[int, int]] = []

        for offset in range(max_stem_length):
            left = i + offset
            right = j - offset

            if left >= right:
                break

            if (left, right) not in pair_set:
                break

            current.append((left, right))

        if current:
            stems.add(tuple(current))

    return sorted(stems, key=lambda item: (len(item), item[0][1] - item[0][0]), reverse=True)


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


def build_dataset_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for item in DATASET:
        sequence = clean_sequence(item["sequence"])
        pairs = candidate_pairs(sequence)
        stems = candidate_stems(sequence)

        rows.append(
            {
                "sequence_id": item["sequence_id"],
                "sequence": sequence,
                "dataset_group": item["dataset_group"],
                "source_type": item["source_type"],
                "length": len(sequence),
                "gc_content_percent": gc_content(sequence),
                "au_content_percent": au_content(sequence),
                "candidate_pair_count": len(pairs),
                "candidate_stem_count": len(stems),
                "reference_status": item["reference_status"],
                "external_validation_status": item["external_validation_status"],
                "notes": item["notes"],
            }
        )

    return rows


def build_rnafold_plan_rows(dataset_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for row in dataset_rows:
        rows.append(
            {
                "sequence_id": row["sequence_id"],
                "sequence": row["sequence"],
                "validation_tool": "ViennaRNA / RNAfold",
                "validation_goal": "Generate reference dot-bracket structure and minimum free energy for comparison.",
                "manual_command_template": f"echo {row['sequence']} | RNAfold",
                "expected_outputs_to_record": "dot_bracket_structure; mfe_energy; base_pair_set",
                "comparison_metrics": "precision; recall; sensitivity; specificity; f1_score",
                "status": "planned_not_yet_executed",
                "safe_note": "This is a validation plan. No RNAfold result is claimed until the command is executed and recorded.",
            }
        )

    return rows


def build_blast_rcsb_rows(dataset_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for row in dataset_rows:
        rows.append(
            {
                "sequence_id": row["sequence_id"],
                "sequence": row["sequence"],
                "blast_goal": "Use NCBI BLAST to explore sequence similarity and biological context.",
                "rcsb_goal": "Use RCSB PDB to search for RNA-related structural references when available.",
                "blast_link": "https://blast.ncbi.nlm.nih.gov/Blast.cgi",
                "rcsb_link": "https://www.rcsb.org/",
                "fields_to_record_later": "top_hit; organism; accession; percent_identity; e_value; related_structure_id; notes",
                "status": "planned_external_review",
                "safe_note": "BLAST/RCSB outputs are context-supporting references, not final proof of RNA folding accuracy.",
            }
        )

    return rows


def build_readiness_summary(dataset_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    total_sequences = len(dataset_rows)
    exact_control_count = sum(1 for row in dataset_rows if row["dataset_group"] == "exact_validation_control")
    expansion_count = sum(1 for row in dataset_rows if row["dataset_group"] == "bioinformatics_expansion")

    total_pairs = sum(int(row["candidate_pair_count"]) for row in dataset_rows)
    total_stems = sum(int(row["candidate_stem_count"]) for row in dataset_rows)

    average_length = round(sum(int(row["length"]) for row in dataset_rows) / total_sequences, 3)
    average_gc = round(sum(float(row["gc_content_percent"]) for row in dataset_rows) / total_sequences, 3)

    return [
        {
            "summary_item": "total_sequences",
            "value": total_sequences,
            "note": "Total RNA sequences currently tracked for validation planning.",
        },
        {
            "summary_item": "exact_validation_control_sequences",
            "value": exact_control_count,
            "note": "Sequences already connected to exact QUBO validation.",
        },
        {
            "summary_item": "bioinformatics_expansion_sequences",
            "value": expansion_count,
            "note": "Additional sequences added for future RNAfold/BLAST/RCSB planning.",
        },
        {
            "summary_item": "average_sequence_length",
            "value": average_length,
            "note": "Average sequence length across the current validation dataset.",
        },
        {
            "summary_item": "average_gc_content_percent",
            "value": average_gc,
            "note": "Average GC content across the current validation dataset.",
        },
        {
            "summary_item": "total_candidate_pairs",
            "value": total_pairs,
            "note": "Total candidate base pairs under current pairing rules.",
        },
        {
            "summary_item": "total_candidate_stems",
            "value": total_stems,
            "note": "Total candidate stems under current stem-generation logic.",
        },
        {
            "summary_item": "external_validation_status",
            "value": "planned",
            "note": "RNAfold, BLAST, and RCSB validation are planned and must be manually verified before claims.",
        },
    ]


def plot_sequence_lengths(dataset_rows: List[Dict[str, Any]]) -> None:
    labels = [row["sequence_id"].replace("EXACT_", "E").replace("BIO_", "B") for row in dataset_rows]
    values = [int(row["length"]) for row in dataset_rows]

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.title("Phase 45 RNA Validation Dataset Sequence Lengths")
    plt.xlabel("Sequence ID")
    plt.ylabel("Length")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(SEQUENCE_LENGTH_FIGURE, dpi=250)
    plt.close()


def plot_gc_content(dataset_rows: List[Dict[str, Any]]) -> None:
    labels = [row["sequence_id"].replace("EXACT_", "E").replace("BIO_", "B") for row in dataset_rows]
    values = [float(row["gc_content_percent"]) for row in dataset_rows]

    plt.figure(figsize=(11, 5))
    plt.bar(labels, values)
    plt.title("Phase 45 RNA Validation Dataset GC Content")
    plt.xlabel("Sequence ID")
    plt.ylabel("GC Content (%)")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(GC_CONTENT_FIGURE, dpi=250)
    plt.close()


def append_once(path: Path, marker: str, content: str) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
    else:
        existing = ""

    if marker in existing:
        return

    updated = existing.rstrip() + "\n\n" + marker + "\n" + content.strip() + "\n"
    path.write_text(updated, encoding="utf-8")


def write_phase45_doc(dataset_rows: List[Dict[str, Any]]) -> None:
    total_sequences = len(dataset_rows)
    exact_control_count = sum(1 for row in dataset_rows if row["dataset_group"] == "exact_validation_control")
    expansion_count = sum(1 for row in dataset_rows if row["dataset_group"] == "bioinformatics_expansion")

    lines = [
        "# Phase 45 — Dataset and External Validation Expansion",
        "",
        "## Purpose",
        "",
        "Phase 45 strengthens the biological validation side of the project.",
        "",
        "The goal is to organize RNA sequences, track reference needs, and prepare external validation through RNAfold/ViennaRNA, BLAST, and RCSB PDB.",
        "",
        "## What This Phase Adds",
        "",
        "- RNA validation dataset table",
        "- external validation dataset tracker",
        "- RNAfold/ViennaRNA validation plan",
        "- BLAST/RCSB reference plan",
        "- dataset readiness summary",
        "- sequence length figure",
        "- GC content figure",
        "",
        "## Generated Tables",
        "",
        "- `data/rna_validation_dataset.csv`",
        "- `results/publication_tables/external_validation_dataset_tracker.csv`",
        "- `results/publication_tables/rnafold_validation_plan.csv`",
        "- `results/publication_tables/blast_rcsb_reference_plan.csv`",
        "- `results/publication_tables/phase45_dataset_readiness_summary.csv`",
        "",
        "## Generated Figures",
        "",
        "- `results/publication_figures/dataset_sequence_lengths.png`",
        "- `results/publication_figures/dataset_gc_content.png`",
        "",
        "## Dataset Summary",
        "",
        f"- Total sequences tracked: {total_sequences}",
        f"- Exact-validation control sequences: {exact_control_count}",
        f"- Bioinformatics expansion sequences: {expansion_count}",
        "",
        "## Validation Plan",
        "",
        "For each sequence, the project should later record:",
        "",
        "- RNAfold dot-bracket output",
        "- RNAfold minimum free energy",
        "- reference base-pair set",
        "- comparison metrics against the QUBO prediction",
        "- BLAST notes where biologically meaningful",
        "- RCSB PDB structure references where available",
        "",
        "## Safe Interpretation",
        "",
        "This phase does not claim that external validation is complete.",
        "",
        "It creates the dataset and validation tracking structure needed to support future claims responsibly.",
        "",
        "RNAfold, BLAST, and RCSB outputs must be manually executed, recorded, and verified before being used as evidence.",
    ]

    PHASE45_DOC.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_results_summary() -> None:
    content = """
# Phase 45 Update — Dataset and External Validation Expansion

Phase 45 expanded the biological validation side of the project.

The project now includes a tracked RNA validation dataset, RNAfold/ViennaRNA validation plan, BLAST/RCSB reference plan, dataset readiness summary, sequence length figure, and GC content figure.

This strengthens the paper direction by separating internal QUBO validation from external biological validation.

Safe interpretation:

This phase creates the structure for external validation. It does not claim that RNAfold, BLAST, or RCSB validation is complete yet.
"""
    append_once(RESULTS_SUMMARY_DOC, PHASE45_MARKER, content)


def update_project_navigation() -> None:
    content = """
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

`python src\\evaluation\\phase45_dataset_external_validation.py`

Safe interpretation:

Phase 45 prepares external validation tracking. It does not claim that RNAfold, BLAST, or RCSB validation has already been completed.
"""
    append_once(PROJECT_NAVIGATION_DOC, PHASE45_MARKER, content)


def main() -> None:
    dataset_rows = build_dataset_rows()
    rnafold_plan_rows = build_rnafold_plan_rows(dataset_rows)
    blast_rcsb_rows = build_blast_rcsb_rows(dataset_rows)
    readiness_rows = build_readiness_summary(dataset_rows)

    write_csv(DATASET_TABLE, dataset_rows)
    write_csv(DATASET_TRACKER_TABLE, dataset_rows)
    write_csv(RNAFOLD_PLAN_TABLE, rnafold_plan_rows)
    write_csv(BLAST_RCSB_PLAN_TABLE, blast_rcsb_rows)
    write_csv(READINESS_SUMMARY_TABLE, readiness_rows)

    plot_sequence_lengths(dataset_rows)
    plot_gc_content(dataset_rows)

    write_phase45_doc(dataset_rows)
    update_results_summary()
    update_project_navigation()

    print("Phase 45 dataset and external validation expansion complete.")
    print(f"Dataset table: {DATASET_TABLE}")
    print(f"Dataset tracker: {DATASET_TRACKER_TABLE}")
    print(f"RNAfold validation plan: {RNAFOLD_PLAN_TABLE}")
    print(f"BLAST/RCSB reference plan: {BLAST_RCSB_PLAN_TABLE}")
    print(f"Readiness summary: {READINESS_SUMMARY_TABLE}")
    print(f"Sequence length figure: {SEQUENCE_LENGTH_FIGURE}")
    print(f"GC content figure: {GC_CONTENT_FIGURE}")
    print(f"Documentation: {PHASE45_DOC}")


if __name__ == "__main__":
    main()