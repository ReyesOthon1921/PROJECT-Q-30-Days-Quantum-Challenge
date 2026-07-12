from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.classical.vienna_rnafold import vienna_status


def build_preflight_report(executable: str = "RNAfold") -> Dict[str, object]:
    return vienna_status(executable=executable)


def format_preflight_report(report: Dict[str, object]) -> str:
    lines = [
        "ViennaRNA preflight check",
        f"RNAfold executable: {report['rnafold_executable']}",
        f"RNAfold CLI available: {'yes' if report['rnafold_cli_available'] else 'no'}",
        f"ViennaRNA Python module available: {'yes' if report['viennarna_python_available'] else 'no'}",
        f"Vienna reference status: {'ready' if report['vienna_reference_ready'] else 'not ready'}",
        f"Recommended action: {report['recommended_action']}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check ViennaRNA availability for the strict classical pipeline.")
    parser.add_argument("--executable", default="RNAfold")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = build_preflight_report(executable=args.executable)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(format_preflight_report(report))


if __name__ == "__main__":
    main()
