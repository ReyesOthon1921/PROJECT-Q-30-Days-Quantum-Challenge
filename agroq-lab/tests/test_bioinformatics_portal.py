from __future__ import annotations

import pytest

from bioinformatics_portal import BioinformaticsError, DEMO_EXPERIMENTS, parse_fasta, sequence_metrics


def test_parse_fasta_combines_lines():
    header, sequence = parse_fasta(">TEST Example\nACGT\nNN\n")
    assert header == "TEST Example"
    assert sequence == "ACGTNN"


def test_parse_fasta_rejects_plain_sequence():
    with pytest.raises(BioinformaticsError):
        parse_fasta("ACGT")


def test_nucleotide_metrics():
    metrics = sequence_metrics("nuccore", "ACGTNN")
    assert metrics["sequence_type"] == "dna"
    assert metrics["length"] == 6
    assert metrics["gc_percent"] == pytest.approx(33.333, abs=0.001)
    assert metrics["ambiguity_count"] == 2


def test_rna_metrics():
    assert sequence_metrics("nuccore", "AUGCUU")["sequence_type"] == "rna"


def test_protein_metrics():
    metrics = sequence_metrics("protein", "MSTX*")
    assert metrics["sequence_type"] == "protein"
    assert metrics["length"] == 5
    assert metrics["ambiguity_count"] == 1


def test_invalid_nucleotide_character():
    with pytest.raises(BioinformaticsError):
        sequence_metrics("nuccore", "ACGT!")


def test_three_demo_experiments_are_defined():
    assert len(DEMO_EXPERIMENTS) == 3
    assert {item["experiment_id"] for item in DEMO_EXPERIMENTS} == {
        "AGQ-PHENO-001", "AGQ-PHENO-002", "AGQ-GENO-003"
    }


def test_demo_claim_boundaries_are_explicit():
    limitations = " ".join(item["limitations"] for item in DEMO_EXPERIMENTS).lower()
    assert "synthetic" in limitations or "computational" in limitations
    assert "causality" in limitations
    assert "new variety" in limitations
