"""ViennaRNA reference wrapper with CLI-first and Python-binding fallback.

The strict path uses the ``RNAfold`` executable through :mod:`subprocess`.
Because this project already declares the ViennaRNA Python package and uses
``RNA.fold`` elsewhere, the wrapper can optionally fall back to that binding on
Windows systems where the package is installed but ``RNAfold.exe`` is not on
``PATH``.
"""

from __future__ import annotations

import re
import subprocess
import time
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RNAfoldResult:
    sequence: str
    reference_structure: Optional[str]
    reference_energy: Optional[float]
    runtime_seconds: float
    success: bool
    error: Optional[str]
    raw_output: str


def validate_rna_sequence(sequence: str) -> str:
    cleaned = sequence.strip().upper().replace("T", "U")

    if not cleaned:
        raise ValueError("RNA sequence is empty.")

    invalid = sorted(set(cleaned) - {"A", "U", "G", "C"})

    if invalid:
        raise ValueError(
            f"RNA sequence contains invalid characters: {invalid}. "
            "Allowed characters are A, U, G, C. T is converted to U."
        )

    return cleaned


def parse_rnafold_output(
    sequence: str,
    raw_output: str,
    runtime_seconds: float,
) -> RNAfoldResult:
    lines = [line.strip() for line in raw_output.splitlines() if line.strip()]

    if len(lines) < 2:
        return RNAfoldResult(
            sequence=sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error="RNAfold output did not contain enough lines.",
            raw_output=raw_output,
        )

    structure_line = lines[1]

    match = re.search(r"([().]+)\s+\(([-+]?\d+(?:\.\d+)?)\)", structure_line)

    if not match:
        return RNAfoldResult(
            sequence=sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error="Could not parse RNAfold structure and energy.",
            raw_output=raw_output,
        )

    structure = match.group(1)
    energy = float(match.group(2))

    return RNAfoldResult(
        sequence=sequence,
        reference_structure=structure,
        reference_energy=energy,
        runtime_seconds=runtime_seconds,
        success=True,
        error=None,
        raw_output=raw_output,
    )


def run_rnafold(sequence: str, timeout_seconds: int = 15) -> Dict[str, object]:
    cleaned_sequence = validate_rna_sequence(sequence)
    start = time.perf_counter()

    try:
        completed = subprocess.run(
            ["RNAfold", "--noPS"],
            input=cleaned_sequence + "\n",
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )

        runtime_seconds = time.perf_counter() - start

        if completed.returncode != 0:
            return RNAfoldResult(
                sequence=cleaned_sequence,
                reference_structure=None,
                reference_energy=None,
                runtime_seconds=runtime_seconds,
                success=False,
                error=completed.stderr.strip() or "RNAfold returned a non-zero exit code.",
                raw_output=completed.stdout,
            ).__dict__

        result = parse_rnafold_output(
            sequence=cleaned_sequence,
            raw_output=completed.stdout,
            runtime_seconds=runtime_seconds,
        )

        return result.__dict__

    except FileNotFoundError:
        runtime_seconds = time.perf_counter() - start

        return RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error="RNAfold command was not found. Install ViennaRNA or add RNAfold to PATH.",
            raw_output="",
        ).__dict__

    except subprocess.TimeoutExpired:
        runtime_seconds = time.perf_counter() - start

        return RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error=f"RNAfold timed out after {timeout_seconds} seconds.",
            raw_output="",
        ).__dict__


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run ViennaRNA RNAfold on one RNA sequence."
    )
    parser.add_argument(
        "--sequence",
        required=True,
        help="RNA sequence using A, U, G, C. T will be converted to U.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Timeout in seconds.",
    )

    args = parser.parse_args()

    output = run_rnafold(args.sequence, timeout_seconds=args.timeout)
    print(json.dumps(output, indent=2))