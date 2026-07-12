from __future__ import annotations

import sys
import types

from src.classical.vienna_rnafold import (
    is_rnafold_cli_available,
    is_viennarna_python_available,
    run_rnafold,
    run_viennarna_python,
    validate_rna_sequence,
    vienna_status,
)


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
        "vienna_method",
    }
    assert expected_keys.issubset(result.keys())
    assert result["sequence"] == "GGGAAAUCC"
    assert isinstance(result["success"], bool)


def test_vienna_status_returns_expected_keys():
    result = vienna_status()
    expected_keys = {
        "rnafold_executable",
        "rnafold_cli_available",
        "viennarna_python_available",
        "vienna_reference_ready",
        "recommended_action",
    }
    assert expected_keys.issubset(result.keys())
    assert isinstance(result["rnafold_cli_available"], bool)
    assert isinstance(result["viennarna_python_available"], bool)


def test_availability_helpers_return_bool():
    assert isinstance(is_rnafold_cli_available(), bool)
    assert isinstance(is_viennarna_python_available(), bool)


def test_python_fallback_with_fake_rna_module(monkeypatch):
    fake_rna = types.SimpleNamespace(fold=lambda sequence: ("(((...)))", -1.23))
    monkeypatch.setitem(sys.modules, "RNA", fake_rna)

    result = run_viennarna_python("GGGAAAUCC")

    assert result["success"] is True
    assert result["reference_structure"] == "(((...)))"
    assert result["reference_energy"] == -1.23
    assert result["vienna_method"] == "viennarna_python"
