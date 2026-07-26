from test_quantum_backend import clean_quantum_db, client, login  # noqa: F401

from q14_support import clear_session, complete_valid_workflow, create_user


def test_viewer_and_field_operator_are_read_only(client):
    login(client)
    create_user("q14viewer", "viewer")
    create_user("q14field", "field_operator")

    for username in ("q14viewer", "q14field"):
        clear_session(client)
        login(client, username=username, password="q14-password")
        assert client.get("/api/quantum/health").status_code == 200
        assert client.get("/api/quantum/validation/summary").status_code == 200
        assert client.post(
            "/api/quantum/datasets/freeze",
            json={
                "name": "blocked",
                "source_tables": ["plots"],
                "permitted_families": ["Q2"],
            },
        ).status_code == 403
        assert client.post(
            "/api/quantum/runs/not-a-run/validate",
            json={},
        ).status_code == 403


def test_researcher_can_run_and_validate_but_cannot_review(client):
    login(client)
    create_user("q14researcher", "researcher")
    clear_session(client)
    login(client, username="q14researcher", password="q14-password")

    _, _, run = complete_valid_workflow(client)
    assert client.post(
        f"/api/quantum/runs/{run['run_id']}/validate",
        json={"include_replay": True},
    ).status_code == 200
    assert client.post(
        f"/api/quantum/runs/{run['run_id']}/replay",
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/quantum/runs/{run['run_id']}/review",
        json={
            "decision": "approved_for_research",
            "notes": "Researcher cannot approve.",
        },
    ).status_code == 403


def test_administrator_can_approve_only_after_gates_pass(client):
    login(client)
    _, _, run = complete_valid_workflow(client)
    response = client.post(
        f"/api/quantum/runs/{run['run_id']}/review",
        json={
            "decision": "approved_for_research",
            "notes": "Administrator reviewed integrity, replay, baseline, and claims.",
        },
    )
    assert response.status_code == 201
