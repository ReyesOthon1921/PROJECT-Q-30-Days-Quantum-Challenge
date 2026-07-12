from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
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
    vienna_method: str


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


def is_rnafold_cli_available(executable: str = "RNAfold") -> bool:
    return shutil.which(executable) is not None


def is_viennarna_python_available() -> bool:
    return importlib.util.find_spec("RNA") is not None


def parse_rnafold_output(
    sequence: str,
    raw_output: str,
    runtime_seconds: float,
    vienna_method: str = "rnafold_cli",
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
            vienna_method=vienna_method,
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
            vienna_method=vienna_method,
        )

    return RNAfoldResult(
        sequence=sequence,
        reference_structure=match.group(1),
        reference_energy=float(match.group(2)),
        runtime_seconds=runtime_seconds,
        success=True,
        error=None,
        raw_output=raw_output,
        vienna_method=vienna_method,
    )


def run_rnafold_cli(
    sequence: str,
    timeout_seconds: int = 15,
    executable: str = "RNAfold",
) -> Dict[str, object]:
    cleaned_sequence = validate_rna_sequence(sequence)
    start = time.perf_counter()

    try:
        completed = subprocess.run(
            [executable, "--noPS"],
            input=cleaned_sequence + "\n",
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        runtime_seconds = time.perf_counter() - start

        if completed.returncode != 0:
            return asdict(RNAfoldResult(
                sequence=cleaned_sequence,
                reference_structure=None,
                reference_energy=None,
                runtime_seconds=runtime_seconds,
                success=False,
                error=completed.stderr.strip() or "RNAfold returned a non-zero exit code.",
                raw_output=completed.stdout,
                vienna_method="rnafold_cli",
            ))

        return asdict(parse_rnafold_output(
            sequence=cleaned_sequence,
            raw_output=completed.stdout,
            runtime_seconds=runtime_seconds,
            vienna_method="rnafold_cli",
        ))

    except FileNotFoundError:
        runtime_seconds = time.perf_counter() - start
        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error=f"{executable} command was not found. Install ViennaRNA or add RNAfold to PATH.",
            raw_output="",
            vienna_method="unavailable",
        ))

    except subprocess.TimeoutExpired:
        runtime_seconds = time.perf_counter() - start
        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error=f"RNAfold timed out after {timeout_seconds} seconds.",
            raw_output="",
            vienna_method="rnafold_cli",
        ))


def run_viennarna_python(sequence: str) -> Dict[str, object]:
    cleaned_sequence = validate_rna_sequence(sequence)
    start = time.perf_counter()

    try:
        import RNA  # type: ignore

        folded = RNA.fold(cleaned_sequence)
        runtime_seconds = time.perf_counter() - start

        if not isinstance(folded, tuple) or len(folded) < 2:
            return asdict(RNAfoldResult(
                sequence=cleaned_sequence,
                reference_structure=None,
                reference_energy=None,
                runtime_seconds=runtime_seconds,
                success=False,
                error="ViennaRNA Python RNA.fold returned an unexpected value.",
                raw_output=str(folded),
                vienna_method="viennarna_python",
            ))

        structure = str(folded[0])
        energy = float(folded[1])

        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=structure,
            reference_energy=energy,
            runtime_seconds=runtime_seconds,
            success=True,
            error=None,
            raw_output=f"RNA.fold({cleaned_sequence}) -> ({structure}, {energy})",
            vienna_method="viennarna_python",
        ))

    except ImportError:
        runtime_seconds = time.perf_counter() - start
        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error="ViennaRNA Python module was not found. Run: python -m pip install viennarna",
            raw_output="",
            vienna_method="unavailable",
        ))

    except Exception as exc:
        runtime_seconds = time.perf_counter() - start
        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=runtime_seconds,
            success=False,
            error=f"ViennaRNA Python folding failed: {exc}",
            raw_output="",
            vienna_method="viennarna_python",
        ))


def run_rnafold(
    sequence: str,
    timeout_seconds: int = 15,
    executable: str = "RNAfold",
    allow_python_fallback: bool = True,
) -> Dict[str, object]:
    cleaned_sequence = validate_rna_sequence(sequence)

    cli_result = run_rnafold_cli(
        cleaned_sequence,
        timeout_seconds=timeout_seconds,
        executable=executable,
    )

    if cli_result.get("success"):
        return cli_result

    if allow_python_fallback:
        python_result = run_viennarna_python(cleaned_sequence)
        if python_result.get("success"):
            return python_result

        return asdict(RNAfoldResult(
            sequence=cleaned_sequence,
            reference_structure=None,
            reference_energy=None,
            runtime_seconds=float(cli_result.get("runtime_seconds") or 0.0)
            + float(python_result.get("runtime_seconds") or 0.0),
            success=False,
            error=(
                "ViennaRNA reference unavailable. "
                f"CLI error: {cli_result.get('error')} "
                f"Python fallback error: {python_result.get('error')}"
            ),
            raw_output=str({"cli": cli_result.get("raw_output"), "python": python_result.get("raw_output")}),
            vienna_method="unavailable",
        ))

    return cli_result


def vienna_status(executable: str = "RNAfold") -> Dict[str, object]:
    cli_available = is_rnafold_cli_available(executable)
    python_available = is_viennarna_python_available()
    ready = cli_available or python_available

    if ready:
        recommended_action = "ViennaRNA reference layer is ready. Run the strict classical pipeline."
    else:
        recommended_action = (
            "Install ViennaRNA CLI or run: python -m pip install viennarna"
        )

    return {
        "rnafold_executable": executable,
        "rnafold_cli_available": cli_available,
        "viennarna_python_available": python_available,
        "vienna_reference_ready": ready,
        "recommended_action": recommended_action,
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run ViennaRNA RNAfold on one RNA sequence.")
    parser.add_argument("--sequence", required=True)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--executable", default="RNAfold")
    parser.add_argument("--no-python-fallback", action="store_true")
    args = parser.parse_args()
    print(json.dumps(
        run_rnafold(
            args.sequence,
            timeout_seconds=args.timeout,
            executable=args.executable,
            allow_python_fallback=not args.no_python_fallback,
        ),
        indent=2,
    ))
