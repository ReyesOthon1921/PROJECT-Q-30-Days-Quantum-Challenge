"""
vienna_benchmark.py

Phase 4 classical benchmark layer.

This module tries to run ViennaRNA through the Python package named RNA.
If ViennaRNA is not installed, the dashboard returns a clean message.
"""

import time

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence


def is_vienna_available() -> bool:
    try:
        import RNA  # type: ignore
        return True
    except ImportError:
        return False


def run_vienna_benchmark(sequence: str) -> dict:
    cleaned = clean_sequence(sequence)

    if not validate_rna_sequence(cleaned):
        return {
            "success": False,
            "vienna_available": is_vienna_available(),
            "error": "Invalid RNA sequence. Use only A, U, G, and C.",
            "sequence": cleaned,
        }

    if not is_vienna_available():
        return {
            "success": False,
            "vienna_available": False,
            "error": "ViennaRNA Python package is not installed yet.",
            "next_step": "Install ViennaRNA later with: python -m pip install ViennaRNA",
            "sequence": cleaned,
            "length": len(cleaned),
        }

    import RNA  # type: ignore

    start_time = time.perf_counter()
    structure, mfe = RNA.fold(cleaned)
    runtime_seconds = round(time.perf_counter() - start_time, 6)

    return {
        "success": True,
        "vienna_available": True,
        "sequence": cleaned,
        "length": len(cleaned),
        "structure": structure,
        "mfe_energy": mfe,
        "runtime_seconds": runtime_seconds,
        "method": "ViennaRNA RNA.fold",
    }


if __name__ == "__main__":
    sequence = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"
    result = run_vienna_benchmark(sequence)

    print("ViennaRNA benchmark summary")
    print("---------------------------")
    for key, value in result.items():
        print(f"{key}: {value}")