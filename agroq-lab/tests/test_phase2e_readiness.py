import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path


def complete_readiness_record():
    return {
        "schema_version": 1,
        "assessment_id": "AGQ-P2E-RD-20260722-01",
        "campaign_id": "AGQ-P2E-FIELD-20260722-01",
        "readiness_checks": {
            f"P2E-RD-{number:02d}": "PASS" for number in range(1, 16)
        },
        "preflight_checks": {
            f"PF-{number:02d}": "PASS" for number in range(1, 16)
        },
        "approvals": {
            "test_lead": "READY",
            "field_operator": "ACCEPTED",
            "independent_reviewer": "AUTHORIZED",
            "site_safety_contact": "APPROVED",
            "adult_lab_supervisor": "APPROVED",
            "backup_recovery_witness": "ACKNOWLEDGED",
        },
        "separation_of_duties_confirmed": True,
        "unresolved_deviations": 0,
    }


def test_readiness_validator_accepts_complete_sanitized_record():
    from scripts.phase2e_readiness import validate_readiness

    result = validate_readiness(complete_readiness_record())

    assert result["record_valid"] is True
    assert result["ready"] is True
    assert result["decision"] == "GO"
    assert result["readiness_counts"] == {
        "pass": 15, "fail": 0, "blocked": 0, "invalid": 0, "missing": 0
    }
    assert result["preflight_counts"] == {
        "pass": 15, "blocked": 0, "invalid": 0, "missing": 0
    }
    assert result["approval_count"] == 6
    assert result["errors"] == []


def test_readiness_validator_fails_closed_when_record_is_missing():
    from scripts.phase2e_readiness import validate_readiness

    result = validate_readiness(None)

    assert result["record_valid"] is False
    assert result["ready"] is False
    assert result["decision"] == "NO-GO"
    assert result["errors"] == ["Private readiness summary is missing."]


def test_readiness_validator_rejects_missing_and_unknown_check_ids():
    from scripts.phase2e_readiness import validate_readiness

    record = complete_readiness_record()
    record["readiness_checks"].pop("P2E-RD-15")
    record["readiness_checks"]["P2E-RD-99"] = "PASS"

    result = validate_readiness(record)

    assert result["record_valid"] is False
    assert result["ready"] is False
    assert "Missing readiness check IDs: P2E-RD-15." in result["errors"]
    assert "Unknown readiness check IDs: P2E-RD-99." in result["errors"]


def test_readiness_validator_blocks_on_fail_or_blocked_status():
    from scripts.phase2e_readiness import validate_readiness

    record = complete_readiness_record()
    record["readiness_checks"]["P2E-RD-03"] = "FAIL"
    record["readiness_checks"]["P2E-RD-09"] = "BLOCKED"
    record["preflight_checks"]["PF-13"] = "BLOCKED"

    result = validate_readiness(record)

    assert result["record_valid"] is True
    assert result["ready"] is False
    assert result["decision"] == "NO-GO"
    assert result["readiness_counts"]["fail"] == 1
    assert result["readiness_counts"]["blocked"] == 1
    assert result["preflight_counts"]["blocked"] == 1


def test_readiness_validator_requires_all_role_decisions_and_separation():
    from scripts.phase2e_readiness import validate_readiness

    record = complete_readiness_record()
    record["approvals"]["independent_reviewer"] = "BLOCKED"
    record["separation_of_duties_confirmed"] = False
    record["unresolved_deviations"] = 2

    result = validate_readiness(record)

    assert result["record_valid"] is True
    assert result["ready"] is False
    assert result["approval_count"] == 5
    assert result["separation_of_duties_confirmed"] is False
    assert result["unresolved_deviations"] == 2


def test_readiness_validator_rejects_private_identity_fields():
    from scripts.phase2e_readiness import validate_readiness

    record = complete_readiness_record()
    record["operator_name"] = "Do not store identities here"

    result = validate_readiness(record)

    assert result["record_valid"] is False
    assert result["ready"] is False
    assert result["errors"] == ["Unknown top-level fields: operator_name."]


def test_readiness_file_loader_returns_only_sanitized_summary(tmp_path):
    from scripts.phase2e_readiness import load_and_validate

    input_path = tmp_path / "private-readiness.json"
    input_path.write_text(json.dumps(complete_readiness_record()), encoding="utf-8")

    result = load_and_validate(input_path)

    assert result["ready"] is True
    assert "assessment_id" not in result
    assert "campaign_id" not in result
    assert "approvals" not in result


def test_readiness_file_loader_fails_closed_for_invalid_json(tmp_path):
    from scripts.phase2e_readiness import load_and_validate

    input_path = tmp_path / "private-readiness.json"
    input_path.write_text("{not-valid-json", encoding="utf-8")

    result = load_and_validate(input_path)

    assert result["record_valid"] is False
    assert result["ready"] is False
    assert result["errors"] == ["Private readiness summary is not valid JSON."]


def test_phase2e_acceptance_supports_documented_direct_command(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            "scripts/phase2e_acceptance.py",
            "--db",
            str(tmp_path / "missing.db"),
            "--readiness",
            "config/phase2e_readiness_summary.example.json",
            "--output",
            str(tmp_path / "report"),
        ],
        cwd=project_root,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert result.stdout.strip() == "Phase 2E: blocked"
    report = json.loads((tmp_path / "report" / "phase2e_acceptance.json").read_text())
    assert report["release_status"] == "blocked"
    assert report["readiness_summary"]["decision"] == "NO-GO"


def test_phase2e_acceptance_fails_closed_for_unusable_database_schema(tmp_path):
    from scripts.phase2e_acceptance import evaluate

    db_path = tmp_path / "field.db"
    sqlite3.connect(db_path).close()

    report = evaluate(db_path, deployment_ready=True, evidence_mode="field")

    assert report["technical_acceptance_passed"] is False
    assert report["release_status"] == "blocked"
    database_gate = next(check for check in report["checks"] if check["id"] == "P2E-DB")
    assert database_gate["passed"] is False
