# Phase 45 — Dataset and External Validation Expansion

## Purpose

Phase 45 strengthens the biological validation side of the project.

The goal is to organize RNA sequences, track reference needs, and prepare external validation through RNAfold/ViennaRNA, BLAST, and RCSB PDB.

## What This Phase Adds

- RNA validation dataset table
- external validation dataset tracker
- RNAfold/ViennaRNA validation plan
- BLAST/RCSB reference plan
- dataset readiness summary
- sequence length figure
- GC content figure

## Generated Tables

- `data/rna_validation_dataset.csv`
- `results/publication_tables/external_validation_dataset_tracker.csv`
- `results/publication_tables/rnafold_validation_plan.csv`
- `results/publication_tables/blast_rcsb_reference_plan.csv`
- `results/publication_tables/phase45_dataset_readiness_summary.csv`

## Generated Figures

- `results/publication_figures/dataset_sequence_lengths.png`
- `results/publication_figures/dataset_gc_content.png`

## Dataset Summary

- Total sequences tracked: 8
- Exact-validation control sequences: 4
- Bioinformatics expansion sequences: 4

## Validation Plan

For each sequence, the project should later record:

- RNAfold dot-bracket output
- RNAfold minimum free energy
- reference base-pair set
- comparison metrics against the QUBO prediction
- BLAST notes where biologically meaningful
- RCSB PDB structure references where available

## Safe Interpretation

This phase does not claim that external validation is complete.

It creates the dataset and validation tracking structure needed to support future claims responsibly.

RNAfold, BLAST, and RCSB outputs must be manually executed, recorded, and verified before being used as evidence.
