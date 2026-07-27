from quantum_runner import (
    deterministic_result_payload,
    run_registered_experiment,
    sha256_json,
)


def test_result_hash_excludes_wall_clock_runtime():
    first = {
        "sequence": "Q2",
        "runtime_seconds": 0.01,
        "solver": {"runtime_seconds": 0.02, "value": 7},
    }
    second = {
        "sequence": "Q2",
        "runtime_seconds": 9.99,
        "solver": {"runtime_seconds": 4.44, "value": 7},
    }
    assert sha256_json(deterministic_result_payload(first)) == sha256_json(
        deterministic_result_payload(second)
    )


def test_same_seed_reproduces_q2_semantic_result_hash():
    configuration = {
        "seed": 301,
        "run_budget": 128,
        "grid_size": 5,
        "sample_budget": 4,
    }
    first = run_registered_experiment(
        "Q2", dataset=None, configuration=configuration
    )["result"]
    second = run_registered_experiment(
        "Q2", dataset=None, configuration=configuration
    )["result"]
    assert first["result_hash_scope"] == "deterministic-v1"
    assert first["result_sha256"] == second["result_sha256"]


def test_changed_seed_changes_stochastic_q2_result_hash():
    first = run_registered_experiment(
        "Q2",
        dataset=None,
        configuration={
            "seed": 301,
            "run_budget": 128,
            "grid_size": 5,
            "sample_budget": 4,
        },
    )["result"]
    second = run_registered_experiment(
        "Q2",
        dataset=None,
        configuration={
            "seed": 907,
            "run_budget": 128,
            "grid_size": 5,
            "sample_budget": 4,
        },
    )["result"]
    assert first["result_sha256"] != second["result_sha256"]
