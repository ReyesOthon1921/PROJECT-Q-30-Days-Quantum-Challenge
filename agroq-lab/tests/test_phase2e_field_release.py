import json


def complete_field_release_record():
    return {
        "schema_version": 1,
        "campaign_id": "AGQ-P2E-FIELD-20260722-01",
        "evidence_mode": "field",
        "manual_release_checks": {
            f"MR-{number:02d}": "PASS" for number in range(1, 10)
        },
        "approvals": {
            "test_lead": "PASS",
            "field_operator": "PASS",
            "independent_reviewer": "APPROVED",
            "site_safety_contact": "APPROVED",
        },
        "automated_suite_passed": True,
        "evidence_index_reviewed": True,
        "source_tree_clean": True,
        "phase3_adapter_read_only_scoped": True,
        "authorization_reference_present": True,
        "unresolved_deviations": 0,
    }


def test_field_release_accepts_complete_sanitized_record():
    from scripts.phase2e_field_release import validate_field_release

    result = validate_field_release(complete_field_release_record())

    assert result["record_valid"] is True
    assert result["accepted"] is True
    assert result["decision"] == "APPROVED"
    assert result["manual_release_counts"] == {
        "pass": 9, "blocked": 0, "invalid": 0, "missing": 0
    }
    assert result["approval_count"] == 4
    assert result["campaign_ref_sha256"]
    assert result["errors"] == []


def test_field_release_blocks_when_any_manual_check_is_blocked():
    from scripts.phase2e_field_release import validate_field_release

    record = complete_field_release_record()
    record["manual_release_checks"]["MR-06"] = "BLOCKED"

    result = validate_field_release(record)

    assert result["record_valid"] is True
    assert result["accepted"] is False
    assert result["decision"] == "BLOCKED"
    assert result["manual_release_counts"]["blocked"] == 1


def test_field_release_requires_field_mode_and_final_controls():
    from scripts.phase2e_field_release import validate_field_release

    record = complete_field_release_record()
    record["evidence_mode"] = "simulation"
    record["approvals"]["independent_reviewer"] = "BLOCKED"
    record["automated_suite_passed"] = False
    record["evidence_index_reviewed"] = False
    record["source_tree_clean"] = False
    record["phase3_adapter_read_only_scoped"] = False
    record["authorization_reference_present"] = False
    record["unresolved_deviations"] = 1

    result = validate_field_release(record)

    assert result["record_valid"] is True
    assert result["accepted"] is False
    assert result["evidence_mode"] == "simulation"
    assert result["approval_count"] == 3
    assert result["unresolved_deviations"] == 1


def test_field_release_rejects_missing_unknown_and_private_fields():
    from scripts.phase2e_field_release import validate_field_release

    record = complete_field_release_record()
    record["manual_release_checks"].pop("MR-09")
    record["manual_release_checks"]["MR-99"] = "PASS"
    record["reviewer_name"] = "Do not store identities here"

    result = validate_field_release(record)

    assert result["record_valid"] is False
    assert result["accepted"] is False
    assert "Missing manual release check IDs: MR-09." in result["errors"]
    assert "Unknown manual release check IDs: MR-99." in result["errors"]
    assert "Unknown top-level fields: reviewer_name." in result["errors"]


def test_field_release_loader_fails_closed_for_invalid_json(tmp_path):
    from scripts.phase2e_field_release import load_and_validate

    input_path = tmp_path / "private-field-release.json"
    input_path.write_text("{not-valid-json", encoding="utf-8")

    result = load_and_validate(input_path)

    assert result["record_valid"] is False
    assert result["accepted"] is False
    assert result["errors"] == ["Private field-release summary is not valid JSON."]


def test_field_release_loader_returns_no_campaign_id_or_approvals(tmp_path):
    from scripts.phase2e_field_release import load_and_validate

    input_path = tmp_path / "private-field-release.json"
    input_path.write_text(json.dumps(complete_field_release_record()), encoding="utf-8")

    result = load_and_validate(input_path)

    assert result["accepted"] is True
    assert "campaign_id" not in result
    assert "approvals" not in result
