"""Strict dot-bracket utilities for Phase 48.

The project already contains :mod:`src.classical.dotbracket`.  This module is a
small compatibility and validation layer rather than a second independent
implementation.  It keeps the existing 0-based convention while adding an
explicit crossing-pair check before reconstruction.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.classical.dotbracket import (
    dotbracket_to_pairs as _existing_dotbracket_to_pairs,
    validate_dotbracket as _existing_validate_dotbracket,
)


def validate_dotbracket(structure: str) -> bool:
    """Return ``True`` for balanced, pseudoknot-free ``.()`` notation."""

    if not isinstance(structure, str):
        return False
    return _existing_validate_dotbracket(structure)


def dotbracket_to_pairs(structure: str) -> list[tuple[int, int]]:
    """Convert dot-bracket notation to sorted 0-based base-pair tuples."""

    return sorted(_existing_dotbracket_to_pairs(structure))


def _pairs_cross(first: tuple[int, int], second: tuple[int, int]) -> bool:
    i, j = first
    k, l = second
    return (i < k < j < l) or (k < i < l < j)


def pairs_to_dotbracket(
    length: int,
    pairs: Iterable[tuple[int, int]],
) -> str:
    """Convert noncrossing 0-based pairs to dot-bracket notation.

    The existing project helper accepts valid nested pairs.  This wrapper first
    rejects duplicate, reused, out-of-range, reversed, or crossing pairs so a
    simple dot-bracket string is never used to silently misrepresent a
    pseudoknot.
    """

    if not isinstance(length, int) or length < 0:
        raise ValueError("length must be a non-negative integer.")

    normalized: list[tuple[int, int]] = []
    seen_pairs: set[tuple[int, int]] = set()
    used_positions: set[int] = set()

    for raw_pair in pairs:
        try:
            i, j = raw_pair
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Each pair must contain two indices: {raw_pair!r}") from exc

        i = int(i)
        j = int(j)

        if not (0 <= i < j < length):
            raise ValueError(
                f"Pair {(i, j)} is invalid for a structure of length {length}."
            )
        if (i, j) in seen_pairs:
            raise ValueError(f"Duplicate pair detected: {(i, j)}")
        if i in used_positions or j in used_positions:
            raise ValueError(f"A nucleotide is used by more than one pair: {(i, j)}")

        seen_pairs.add((i, j))
        used_positions.update((i, j))
        normalized.append((i, j))

    normalized.sort()

    for index, first in enumerate(normalized):
        for second in normalized[index + 1 :]:
            if _pairs_cross(first, second):
                raise ValueError(
                    "Crossing pairs cannot be represented with simple dot-bracket "
                    f"notation: {first} crosses {second}."
                )

    symbols = ["."] * length
    for i, j in normalized:
        symbols[i] = "("
        symbols[j] = ")"
    return "".join(symbols)
