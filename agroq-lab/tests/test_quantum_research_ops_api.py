import io
import zipfile

from test_quantum_backend import clean_quantum_db, client, login  # noqa: F401

from q14_support import (
    clear_session,
    complete_valid_workflow,
    create_user,
)


def test_q15_complete_research_operations_and_release_api(client):
    login(client)
    _, _, run = complete_valid_workflow(client)

    ensured = client.post(f"/api/quantum/runs/{run['run_id']}/operation")
    assert ensured.status_code == 200
    operation = ensured.get_json()["operation"]
    assert operation["lifecycle_state"] == "Completed"

    under_review = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Under review",
            "reason": "Run completed and evidence is ready for independent review.",
            "research_notes": "Q2 exact, annealing, and QAOA outputs were compared.",
            "limitations": "Synthetic simulator benchmark; no hardware or advantage claim.",
        },
    )
    assert under_review.status_code == 200

    create_user("q15reviewer", "administrator")
    clear_session(client)
    login(client, username="q15reviewer", password="q14-password")

    approved = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Approved for research",
            "reason": "Independent Q14 replay and scientific gates passed.",
            "research_notes": "Q2 exact, annealing, and QAOA outputs were compared.",
            "limitations": "Synthetic simulator benchmark; no hardware or advantage claim.",
        },
    )
    assert approved.status_code == 200
    approved_operation = approved.get_json()["operation"]
    assert approved_operation["reviewer_id"] == "AGQ-USER-Q15REVIEWER"
    assert approved_operation["lifecycle_state"] == "Approved for research"

    evidence = client.get(
        f"/api/quantum/operations/{operation['operation_id']}/evidence.zip"
    )
    assert evidence.status_code == 200
    assert evidence.headers["X-AgroQ-SHA256"]
    with zipfile.ZipFile(io.BytesIO(evidence.data)) as archive:
        names = set(archive.namelist())
        assert "SHA256SUMS.txt" in names
        assert "experiment.json" in names
        assert "validation_history.json" in names
        assert "review_history.json" in names

    checklist = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/checklist",
        json={
            "manual": {
                "limitations_disclosed": True,
                "evidence_reviewed": True,
                "rollback_plan_documented": True,
                "release_notes_complete": True,
            }
        },
    )
    assert checklist.status_code == 200
    assert checklist.get_json()["release_checklist"]["complete"] is True

    released = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Released",
            "reason": "All automatic and manual release controls are complete.",
            "research_notes": "Q2 exact, annealing, and QAOA outputs were compared.",
            "limitations": "Synthetic simulator benchmark; no hardware or advantage claim.",
        },
    )
    assert released.status_code == 200
    assert released.get_json()["operation"]["lifecycle_state"] == "Released"

    detail = client.get(
        f"/api/quantum/operations/{operation['operation_id']}"
    )
    assert detail.status_code == 200
    detail_payload = detail.get_json()
    assert detail_payload["operation"]["history"]
    assert detail_payload["operation"]["evidence_bundles"]
    assert detail_payload["release_checklist"]["complete"] is True

    summary = client.get("/api/quantum/operations")
    assert summary.status_code == 200
    assert summary.get_json()["counts"]["Released"] == 1


def test_q15_researcher_cannot_self_approve(client):
    login(client)
    create_user("q15researcher", "researcher")
    clear_session(client)
    login(client, username="q15researcher", password="q14-password")
    _, _, run = complete_valid_workflow(client)

    ensured = client.post(f"/api/quantum/runs/{run['run_id']}/operation")
    operation = ensured.get_json()["operation"]
    assert client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Under review",
            "reason": "Ready for independent review.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
    ).status_code == 200

    attempt = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Approved for research",
            "reason": "Self approval attempt.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
    )
    assert attempt.status_code == 403


def test_q15_viewer_is_read_only(client):
    login(client)
    _, _, run = complete_valid_workflow(client)
    client.post(f"/api/quantum/runs/{run['run_id']}/operation")

    create_user("q15viewer", "viewer")
    clear_session(client)
    login(client, username="q15viewer", password="q14-password")

    assert client.get("/api/quantum/operations").status_code == 200
    assert client.post(
        f"/api/quantum/runs/{run['run_id']}/operation"
    ).status_code == 403
    assert client.post(
        "/api/quantum/operations/not-an-operation/checklist",
        json={"manual": {}},
    ).status_code == 403


def test_q15_release_is_blocked_before_checklist_and_evidence(client):
    login(client)
    _, _, run = complete_valid_workflow(client)
    operation = client.post(
        f"/api/quantum/runs/{run['run_id']}/operation"
    ).get_json()["operation"]
    client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Under review",
            "reason": "Review requested.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
    )

    create_user("q15reviewer2", "administrator")
    clear_session(client)
    login(client, username="q15reviewer2", password="q14-password")
    approved = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Approved for research",
            "reason": "Independent validation passed.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
    )
    assert approved.status_code == 200

    release = client.post(
        f"/api/quantum/operations/{operation['operation_id']}/transition",
        json={
            "to_state": "Released",
            "reason": "Premature release.",
            "research_notes": "Research notes.",
            "limitations": "Known limitations.",
        },
    )
    assert release.status_code == 409
    assert "checklist" in release.get_json()["error"].lower()
