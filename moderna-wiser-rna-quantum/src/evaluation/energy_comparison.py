"""Diagnostic ViennaRNA-MFE versus QUBO-objective comparison."""

from __future__ import annotations

from typing import Any


def compare_energy(reference_energy: float, qubo_energy: float) -> dict[str, Any]:
    """Compare numerical values without asserting physical equivalence."""

    reference = float(reference_energy)
    qubo = float(qubo_energy)
    difference = qubo - reference

    return {
        "reference_energy": reference,
        "qubo_energy": qubo,
        "energy_difference": difference,
        "absolute_energy_difference": abs(difference),
        "note": (
            "Diagnostic only: ViennaRNA MFE is a thermodynamic free-energy "
            "estimate, while the QUBO value is an optimization objective in a "
            "different scoring system. The values are not physically equivalent "
            "and must not be interpreted as the same unit or model."
        ),
    }
