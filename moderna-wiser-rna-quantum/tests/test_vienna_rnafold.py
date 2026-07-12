from __future__ import annotations

from src.classical.vienna_rnafold import run_rnafold, validate_rna_sequence


def test_validate_rna_sequence_accepts_rna():
    assert validate_rna_sequence("AUGC") == "AUGC"


def test_validate_rna_sequence_converts_t_to_u():
    assert validate_rna_sequence("ATGC") == "AUGC"


def test_validate_rna_sequence_rejects_invalid_letters():
    try:
        validate_rna_sequence("AUGX")
    except ValueError as exc:
        assert "invalid characters" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid RNA sequence.")


def test_run_rnafold_returns_expected_keys():
    result = run_rnafold("GGGAAAUCC")

    expected_keys = {
        "sequence",
        "reference_structure",
        "reference_energy",
        "runtime_seconds",
        "success",
        "error",
        "raw_output",
    }

    assert expected_keys.issubset(result.keys())
    assert result["sequence"] == "GGGAAAUCC"
    assert isinstance(result["success"], bool)