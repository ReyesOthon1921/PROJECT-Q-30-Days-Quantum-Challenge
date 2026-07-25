import pytest

from quantum_runner import SUPPORTED_SEQUENCES, run_registered_experiment


@pytest.mark.parametrize(
    "sequence,configuration",
    [
        ("Q2", {"seed": 301, "run_budget": 128, "grid_size": 5, "sample_budget": 4}),
        ("Q3", {"seed": 301, "run_budget": 128, "grid_size": 5}),
        ("Q4", {"seed": 301, "run_budget": 128, "grid_size": 5}),
        ("Q5", {"seed": 301}),
        ("Q6", {"seed": 301}),
        ("Q7", {"seed": 301, "shots_per_circuit": 32}),
        ("Q8", {"seed": 301}),
        ("Q9", {"grid_points": 181}),
        ("Q10", {}),
    ],
)
def test_all_server_sequences_execute_with_claim_boundaries(sequence, configuration):
    execution = run_registered_experiment(
        sequence,
        dataset=None,
        configuration=configuration,
    )
    result = execution["result"]
    assert result["sequence"] == sequence
    assert result["result_sha256"].startswith("sha256:")
    assert execution["artifacts"]
    assert result["solver_results"]

    controls = result["controls"]
    assert controls.get("advantage_claim", False) is False
    assert controls.get("hardware_used", False) is False
    assert controls.get("operational_dependency", False) is False


def test_supported_server_sequence_contract_is_complete():
    assert SUPPORTED_SEQUENCES == {
        "Q2",
        "Q3",
        "Q4",
        "Q5",
        "Q6",
        "Q7",
        "Q8",
        "Q9",
        "Q10",
    }


def test_unsupported_sequence_fails_closed():
    with pytest.raises(ValueError):
        run_registered_experiment(
            "Q99",
            dataset=None,
            configuration={},
        )
