from __future__ import annotations

from typing import List, Tuple

BasePair = Tuple[int, int]


def validate_dotbracket(structure: str) -> bool:
    stack: List[int] = []
    for char in structure:
        if char == "(":
            stack.append(1)
        elif char == ")":
            if not stack:
                return False
            stack.pop()
        elif char == ".":
            continue
        else:
            return False
    return len(stack) == 0


def dotbracket_to_pairs(structure: str) -> List[BasePair]:
    if not validate_dotbracket(structure):
        raise ValueError(f"Invalid dot-bracket structure: {structure}")

    stack: List[int] = []
    pairs: List[BasePair] = []
    for index, char in enumerate(structure):
        if char == "(":
            stack.append(index)
        elif char == ")":
            pairs.append((stack.pop(), index))
    return sorted(pairs)


def pairs_to_dotbracket(length: int, pairs: List[BasePair]) -> str:
    if length <= 0:
        raise ValueError("Structure length must be positive.")

    structure = ["."] * length
    used_positions = set()

    for left, right in pairs:
        if left < 0 or right < 0:
            raise ValueError(f"Pair contains negative index: {(left, right)}")
        if left >= length or right >= length:
            raise ValueError(f"Pair is outside structure length {length}: {(left, right)}")
        if left >= right:
            raise ValueError(f"Pair must satisfy left < right: {(left, right)}")
        if left in used_positions or right in used_positions:
            raise ValueError(f"Position reused in base-pair list: {(left, right)}")
        structure[left] = "("
        structure[right] = ")"
        used_positions.add(left)
        used_positions.add(right)

    dotbracket = "".join(structure)
    if not validate_dotbracket(dotbracket):
        raise ValueError(f"Generated invalid dot-bracket structure: {dotbracket}")
    return dotbracket


def pair_set(structure: str) -> set[BasePair]:
    return set(dotbracket_to_pairs(structure))
