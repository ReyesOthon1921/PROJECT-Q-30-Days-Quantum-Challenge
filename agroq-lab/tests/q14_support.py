from werkzeug.security import generate_password_hash

from app import get_db


def clear_session(client):
    with client.session_transaction() as session:
        session.clear()


def create_user(username, role, password="q14-password"):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO users(
                user_id, username, display_name, password_hash, role,
                site_id, active, created_at
            ) VALUES(?,?,?,?,?,?,?,?)""",
            (
                f"AGQ-USER-{username.upper()}",
                username,
                f"Q14 {role}",
                generate_password_hash(password),
                role,
                "AGQ-SITE-001",
                1,
                "2026-01-01T00:00:00+00:00",
            ),
        )


def freeze_dataset(client):
    response = client.post(
        "/api/quantum/datasets/freeze",
        json={
            "name": "Q14 validation snapshot",
            "source_tables": ["plots", "observations"],
            "permitted_families": ["Q2"],
        },
    )
    assert response.status_code == 201
    return response.get_json()["dataset"]


def register_experiment(client, dataset_id):
    response = client.post(
        "/api/quantum/experiments",
        json={
            "experimentId": "AGQ-Q14-Q2-TEST",
            "sequence": "Q2",
            "title": "Q14 persistent validation test",
            "problemFamily": "Constrained sample selection",
            "sourceIds": ["QRS-001", "QRS-002", "QRS-003"],
            "status": "Registered",
            "runType": "quantum-simulator",
            "algorithm": "Exact + annealing + QAOA",
            "dataset_id": dataset_id,
            "formulation": {
                "type": "QUBO",
                "variables": 6,
                "constraints": 1,
            },
            "codeCommit": "q14-test",
            "claimControls": {
                "advantageClaim": False,
                "operationalDependency": False,
            },
        },
    )
    assert response.status_code == 201
    return response.get_json()["experiment"]


def execute_run(client, experiment_id="AGQ-Q14-Q2-TEST"):
    response = client.post(
        f"/api/quantum/experiments/{experiment_id}/runs",
        json={
            "configuration": {
                "seed": 301,
                "run_budget": 256,
                "grid_size": 5,
                "sample_budget": 4,
            },
            "run_budget": {
                "solution_samples": 256,
                "matched_across_solvers": True,
            },
        },
    )
    assert response.status_code == 201
    return response.get_json()["run"]


def complete_valid_workflow(client):
    dataset = freeze_dataset(client)
    experiment = register_experiment(client, dataset["dataset_id"])
    run = execute_run(client, experiment["experiment_id"])
    return dataset, experiment, run
