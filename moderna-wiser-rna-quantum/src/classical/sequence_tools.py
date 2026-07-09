"""
sequence_tools.py

Phase 3 RNA sequence preprocessing.
"""

VALID_RNA_BASES = {"A", "U", "G", "C"}

PAIR_TYPES = {
    ("A", "U"): "A-U",
    ("U", "A"): "U-A",
    ("G", "C"): "G-C",
    ("C", "G"): "C-G",
    ("G", "U"): "G-U wobble",
    ("U", "G"): "U-G wobble",
}


def clean_sequence(sequence: str) -> str:
    return "".join(sequence.upper().split())


def validate_rna_sequence(sequence: str) -> bool:
    cleaned = clean_sequence(sequence)

    if len(cleaned) == 0:
        return False

    return all(base in VALID_RNA_BASES for base in cleaned)


def invalid_bases(sequence: str) -> list:
    cleaned = clean_sequence(sequence)
    return sorted(set(base for base in cleaned if base not in VALID_RNA_BASES))


def calculate_gc_content(sequence: str) -> float:
    cleaned = clean_sequence(sequence)

    if len(cleaned) == 0:
        return 0.0

    gc_count = cleaned.count("G") + cleaned.count("C")
    return round((gc_count / len(cleaned)) * 100, 2)


def find_valid_base_pair_candidates(sequence: str, min_loop_length: int = 3) -> list:
    cleaned = clean_sequence(sequence)
    candidates = []

    for i in range(len(cleaned)):
        for j in range(i + min_loop_length + 1, len(cleaned)):
            pair = (cleaned[i], cleaned[j])

            if pair in PAIR_TYPES:
                candidates.append(
                    {
                        "i": i,
                        "j": j,
                        "left_base": cleaned[i],
                        "right_base": cleaned[j],
                        "pair_type": PAIR_TYPES[pair],
                    }
                )

    return candidates


def count_pair_types(candidates: list) -> dict:
    counts = {
        "A-U": 0,
        "U-A": 0,
        "G-C": 0,
        "C-G": 0,
        "G-U wobble": 0,
        "U-G wobble": 0,
    }

    for candidate in candidates:
        pair_type = candidate["pair_type"]
        counts[pair_type] += 1

    return counts


def summarize_sequence(sequence: str) -> dict:
    cleaned = clean_sequence(sequence)
    valid = validate_rna_sequence(cleaned)

    if not valid:
        return {
            "sequence": cleaned,
            "length": len(cleaned),
            "is_valid_rna": False,
            "invalid_bases": invalid_bases(cleaned),
            "gc_content_percent": None,
            "candidate_pair_count": 0,
            "pair_type_counts": {},
            "first_10_candidates": [],
        }

    candidates = find_valid_base_pair_candidates(cleaned)

    return {
        "sequence": cleaned,
        "length": len(cleaned),
        "is_valid_rna": True,
        "invalid_bases": [],
        "gc_content_percent": calculate_gc_content(cleaned),
        "candidate_pair_count": len(candidates),
        "pair_type_counts": count_pair_types(candidates),
        "first_10_candidates": candidates[:10],
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    summary = summarize_sequence(sequence)

    print("RNA sequence preprocessing summary")
    print("----------------------------------")
    for key, value in summary.items():
        print(f"{key}: {value}")