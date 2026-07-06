"""
dotbracket.py

Phase 1 classical RNA foundation.

This module handles:
1. dot-bracket validation
2. base-pair extraction
3. simple structure summaries

Dot-bracket notation:
    . = unpaired nucleotide
    ( = opening paired nucleotide
    ) = closing paired nucleotide
"""

from typing import List, Tuple


BasePair = Tuple[int, int]


def validate_dotbracket(structure: str) -> bool:
    """
    Check whether a dot-bracket structure is balanced and only uses '.', '(' and ')'.

    Example:
        "....(((...)))...." -> True
        "....(((...))....." -> False
    """
    stack = []

    for char in structure:
        if char not in ".()":
            return False

        if char == "(":
            stack.append(char)

        elif char == ")":
            if not stack:
                return False
            stack.pop()

    return len(stack) == 0


def dotbracket_to_pairs(structure: str) -> List[BasePair]:
    """
    Convert dot-bracket notation into a list of base-pair index tuples.

    Uses 0-based indexing.

    Example:
        structure = "..((..)).."
        output = [(2, 7), (3, 6)]
    """
    if not validate_dotbracket(structure):
        raise ValueError("Invalid dot-bracket structure.")

    stack = []
    pairs = []

    for index, char in enumerate(structure):
        if char == "(":
            stack.append(index)

        elif char == ")":
            left_index = stack.pop()
            right_index = index
            pairs.append((left_index, right_index))

    return pairs


def pairs_to_dotbracket(length: int, pairs: List[BasePair]) -> str:
    """
    Convert a list of base pairs back into dot-bracket notation.

    Example:
        length = 10
        pairs = [(2, 7), (3, 6)]
        output = "..((..)).."
    """
    structure = ["."] * length

    for i, j in pairs:
        if i < 0 or j < 0 or i >= length or j >= length:
            raise ValueError(f"Pair {(i, j)} is outside the sequence length.")

        if i >= j:
            raise ValueError(f"Invalid pair order: {(i, j)}")

        if structure[i] != "." or structure[j] != ".":
            raise ValueError(f"Base already paired in pair {(i, j)}")

        structure[i] = "("
        structure[j] = ")"

    return "".join(structure)


def count_pairs(structure: str) -> int:
    """
    Count the number of base pairs in a dot-bracket structure.
    """
    return len(dotbracket_to_pairs(structure))


def summarize_structure(sequence: str, structure: str) -> dict:
    """
    Return a small summary dictionary for a sequence and structure.
    """
    if len(sequence) != len(structure):
        raise ValueError("Sequence and structure must have the same length.")

    pairs = dotbracket_to_pairs(structure)

    return {
        "sequence": sequence,
        "structure": structure,
        "length": len(sequence),
        "num_pairs": len(pairs),
        "pairs": pairs,
        "is_valid_dotbracket": validate_dotbracket(structure),
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    structure = ".................(((....)))................."

    summary = summarize_structure(sequence, structure)

    print("Dot-bracket summary")
    print("-------------------")
    for key, value in summary.items():
        print(f"{key}: {value}")