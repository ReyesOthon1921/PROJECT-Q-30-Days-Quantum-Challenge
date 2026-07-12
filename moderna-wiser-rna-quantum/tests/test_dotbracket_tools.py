import pytest

from src.classical.dotbracket_tools import (
    dotbracket_to_pairs,
    pairs_to_dotbracket,
    validate_dotbracket,
)


def test_valid_structure_passes() -> None:
    assert validate_dotbracket("((...))") is True


def test_invalid_structure_fails() -> None:
    assert validate_dotbracket("(()") is False
    assert validate_dotbracket("(.x.)") is False


def test_dotbracket_to_pairs_uses_zero_based_indices() -> None:
    assert dotbracket_to_pairs("((...))") == [(0, 6), (1, 5)]


def test_pairs_to_dotbracket() -> None:
    assert pairs_to_dotbracket(7, [(0, 6), (1, 5)]) == "((...))"


def test_round_trip() -> None:
    structure = ".((...)).."
    assert pairs_to_dotbracket(len(structure), dotbracket_to_pairs(structure)) == structure


def test_crossing_pairs_are_rejected() -> None:
    with pytest.raises(ValueError):
        pairs_to_dotbracket(6, [(0, 3), (1, 5)])
