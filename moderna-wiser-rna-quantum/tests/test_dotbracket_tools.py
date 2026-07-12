from __future__ import annotations

import pytest

from src.classical.dotbracket_tools import (
    dotbracket_to_pairs,
    pairs_to_dotbracket,
    validate_dotbracket,
)


def test_validate_dotbracket_valid_structure():
    assert validate_dotbracket("((...))") is True


def test_validate_dotbracket_invalid_unbalanced_structure():
    assert validate_dotbracket("((...)") is False


def test_validate_dotbracket_invalid_character():
    assert validate_dotbracket("((..x))") is False


def test_dotbracket_to_pairs():
    assert dotbracket_to_pairs("((...))") == [(0, 6), (1, 5)]


def test_pairs_to_dotbracket():
    pairs = [(0, 6), (1, 5)]
    assert pairs_to_dotbracket(7, pairs) == "((...))"


def test_round_trip_dotbracket_pairs():
    structure = "((...))"
    pairs = dotbracket_to_pairs(structure)
    reconstructed = pairs_to_dotbracket(len(structure), pairs)

    assert reconstructed == structure


def test_pairs_to_dotbracket_rejects_reused_position():
    with pytest.raises(ValueError):
        pairs_to_dotbracket(6, [(0, 5), (0, 4)])


def test_dotbracket_to_pairs_rejects_invalid_structure():
    with pytest.raises(ValueError):
        dotbracket_to_pairs("((...)")