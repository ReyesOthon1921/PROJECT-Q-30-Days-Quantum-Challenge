from __future__ import annotations

from typing import Dict, Optional

ENERGY_NOTE = (
    "Diagnostic comparison only. ViennaRNA MFE energy and QUBO energy are "
    "different scoring systems and should not be treated as physically equivalent."
)


def compare_energy(reference_energy: Optional[float], qubo_energy: Optional[float]) -> Dict[str, object]:
    reference_available = reference_energy is not None
    qubo_available = qubo_energy is not None

    if not reference_available or not qubo_available:
        return {
            "reference_energy": reference_energy,
            "qubo_energy": qubo_energy,
            "reference_available": reference_available,
            "qubo_available": qubo_available,
            "comparison_available": False,
            "energy_difference": None,
            "absolute_energy_difference": None,
            "note": ENERGY_NOTE,
        }

    energy_difference = float(qubo_energy) - float(reference_energy)
    return {
        "reference_energy": float(reference_energy),
        "qubo_energy": float(qubo_energy),
        "reference_available": True,
        "qubo_available": True,
        "comparison_available": True,
        "energy_difference": energy_difference,
        "absolute_energy_difference": abs(energy_difference),
        "note": ENERGY_NOTE,
    }


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Compare ViennaRNA MFE energy against QUBO energy.")
    parser.add_argument("--reference-energy", type=float, required=True)
    parser.add_argument("--qubo-energy", type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(compare_energy(args.reference_energy, args.qubo_energy), indent=2))
