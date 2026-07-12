"""ViennaRNA reference wrapper with CLI-first and Python-binding fallback.

The strict path uses the ``RNAfold`` executable through :mod:`subprocess`.
Because this project already declares the ViennaRNA Python package and uses
``RNA.fold`` elsewhere, the wrapper can optionally fall back to that binding on
Windows systems where the package is installed but ``RNAfold.exe`` is not on
``PATH``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
from typing import Any

from src.classical.sequence_tools import clean_sequence, validate_rna_sequence

_STRUCTURE_RE = re.compile(
    r"(?P<structure>[().]+)\s+\(\s*(?P<energy>[-+]?\d+(?:\.\d+)?)\s*\)"
)


def _base_result(sequence: str) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "reference_structure": None,
        "reference_energy": None,
        "runtime_seconds": 0.0,
        "success": False,
        "status": "pending",
        "error": None,
        "backend": None,
        "warnings": [],
    }


def _parse_rnafold_stdout(stdout: str, sequence_length: int) -> tuple[str, float]:
    match = None
    for line in stdout.splitlines():
        candidate = _STRUCTURE_RE.search(line.strip())
        if candidate:
            match = candidate

    if match is None:
        raise ValueError(
            "RNAfold finished, but its structure/energy output could not be parsed. "
            f"Raw stdout: {stdout.strip()!r}"
        )

    structure = match.group("structure")
    if len(structure) != sequence_length:
        raise ValueError(
            "RNAfold returned a structure whose length does not match the input "
            f"sequence ({len(structure)} != {sequence_length})."
        )

    return structure, float(match.group("energy"))


def _run_cli(
    sequence: str,
    executable: str,
    timeout_seconds: float,
) -> dict[str, Any]:
    resolved = shutil.which(executable)
    if resolved is None:
        raise FileNotFoundError(
            f"RNAfold executable '{executable}' was not found on PATH."
        )

    completed = subprocess.run(
        [resolved, "--noPS"],
        input=f"{sequence}\n",
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )

    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "No stderr output was produced."
        raise RuntimeError(
            f"RNAfold exited with code {completed.returncode}: {stderr}"
        )

    structure, energy = _parse_rnafold_stdout(completed.stdout, len(sequence))
    return {
        "reference_structure": structure,
        "reference_energy": energy,
        "backend": "RNAfold CLI",
        "command": [resolved, "--noPS"],
    }


def _run_python_binding(sequence: str) -> dict[str, Any]:
    try:
        import RNA  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "ViennaRNA Python binding is not installed."
        ) from exc

    structure, energy = RNA.fold(sequence)
    structure = str(structure)

    if len(structure) != len(sequence):
        raise ValueError(
            "ViennaRNA Python binding returned a structure whose length does not "
            f"match the input sequence ({len(structure)} != {len(sequence)})."
        )

    return {
        "reference_structure": structure,
        "reference_energy": float(energy),
        "backend": "ViennaRNA Python RNA.fold",
        "command": None,
    }


def run_rnafold(
    sequence: str,
    executable: str = "RNAfold",
    timeout_seconds: float = 60.0,
    allow_python_fallback: bool = True,
) -> dict[str, Any]:
    """Return a stable ViennaRNA reference dictionary for one RNA sequence.

    Failures are returned as data instead of being raised so the surrounding
    pipeline can still save a reproducible partial report.
    """

    started = time.perf_counter()
    cleaned = clean_sequence(sequence)
    result = _base_result(cleaned)

    if not validate_rna_sequence(cleaned):
        result["status"] = "invalid_input"
        result["error"] = "Invalid RNA sequence. Use only A, U, G, and C."
        result["runtime_seconds"] = round(time.perf_counter() - started, 6)
        return result

    cli_error: str | None = None

    try:
        cli_result = _run_cli(cleaned, executable, timeout_seconds)
        result.update(cli_result)
        result["success"] = True
        result["status"] = "success"
        result["runtime_seconds"] = round(time.perf_counter() - started, 6)
        return result
    except subprocess.TimeoutExpired:
        cli_error = f"RNAfold timed out after {timeout_seconds:.1f} seconds."
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        cli_error = str(exc)

    if allow_python_fallback:
        try:
            binding_result = _run_python_binding(cleaned)
            result.update(binding_result)
            result["success"] = True
            result["status"] = "success_with_fallback"
            if cli_error:
                result["warnings"].append(
                    f"RNAfold CLI was unavailable or failed: {cli_error}"
                )
            result["runtime_seconds"] = round(time.perf_counter() - started, 6)
            return result
        except (ImportError, RuntimeError, ValueError) as exc:
            binding_error = str(exc)
        except Exception as exc:  # Defensive boundary around an external package.
            binding_error = f"ViennaRNA Python binding failed: {exc}"
    else:
        binding_error = "Python-binding fallback was disabled."

    result["status"] = "unavailable"
    result["error"] = (
        f"RNAfold CLI error: {cli_error or 'unknown error'} "
        f"Python binding error: {binding_error}"
    )
    result["runtime_seconds"] = round(time.perf_counter() - started, 6)
    return result
