from __future__ import annotations

import math
from src.evaluation.energy_comparison import compare_energy


def test_compare_energy_when_both_values_exist():
    result = compare_energy(reference_energy=-2.5, qubo_energy=-1.0)
    assert result["comparison_available"] is True
    assert math.isclose(result["energy_difference"], 1.5)
    assert "Diagnostic comparison only" in result["note"]


def test_compare_energy_when_reference_missing():
    result = compare_energy(reference_energy=None, qubo_energy=-1.0)
    assert result["comparison_available"] is False
    assert result["energy_difference"] is None
