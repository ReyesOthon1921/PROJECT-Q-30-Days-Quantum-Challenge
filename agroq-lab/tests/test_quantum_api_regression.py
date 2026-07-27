from test_quantum_backend import clean_quantum_db, client, login  # noqa: F401

from q14_support import complete_valid_workflow


def test_complete_q11_q14_api_regression(client):
    login(client)

    health = client.get("/api/quantum/health")
    assert health.status_code == 200
    assert health.get_json()["ok"] is True

    sources = client.get("/api/quantum/sources")
    assert sources.status_code == 200
    assert len(sources.get_json()["sources"]) == 22

    assert client.get("/api/quantum/datasets").status_code == 200

    dataset, experiment, run = complete_valid_workflow(client)

    assert client.get(
        f"/api/quantum/datasets/{dataset['dataset_id']}"
    ).status_code == 200

    verified = client.post(
        f"/api/quantum/datasets/{dataset['dataset_id']}/verify",
        json={},
    )
    assert verified.status_code == 200
    assert verified.get_json()["validation"]["status"] in {"passed", "warning"}

    assert client.get("/api/quantum/experiments").status_code == 200
    assert client.get(
        f"/api/quantum/experiments/{experiment['experiment_id']}"
    ).status_code == 200

    assert client.post(
        f"/api/quantum/experiments/{experiment['experiment_id']}/dataset",
        json={"dataset_id": dataset["dataset_id"]},
    ).status_code == 200

    detail = client.get(f"/api/quantum/runs/{run['run_id']}")
    assert detail.status_code == 200
    assert detail.get_json()["run"]["status"] == "completed"

    validation = client.post(
        f"/api/quantum/runs/{run['run_id']}/validate",
        json={"include_replay": True},
    )
    assert validation.status_code == 200
    assert validation.get_json()["validation"]["status"] == "passed"

    replay = client.post(
        f"/api/quantum/runs/{run['run_id']}/replay",
        json={},
    )
    assert replay.status_code == 200
    assert replay.get_json()["validation"]["status"] == "passed"

    history = client.get(f"/api/quantum/runs/{run['run_id']}/validation")
    assert history.status_code == 200
    assert history.get_json()["events"]

    artifacts = client.get(f"/api/quantum/runs/{run['run_id']}/artifacts")
    assert artifacts.status_code == 200
    artifact_id = artifacts.get_json()["artifacts"][0]["artifact_id"]

    download = client.get(f"/api/quantum/artifacts/{artifact_id}")
    assert download.status_code == 200
    assert download.headers["X-AgroQ-SHA256"].startswith("sha256:")

    summary = client.get("/api/quantum/validation/summary")
    assert summary.status_code == 200
    payload = summary.get_json()
    assert payload["schema_version"] == "AGROQ-QVALIDATION-1.0"
    assert payload["runs"]
    assert payload["datasets"]

    review = client.post(
        f"/api/quantum/runs/{run['run_id']}/review",
        json={
            "decision": "approved_for_research",
            "notes": "All Q14 scientific gates passed.",
        },
    )
    assert review.status_code == 201
