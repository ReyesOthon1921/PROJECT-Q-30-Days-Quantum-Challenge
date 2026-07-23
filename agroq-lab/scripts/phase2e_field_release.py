"""Validate the private post-field Phase 2E release decision.

This module emits only a sanitized summary. The signed private field-validation
record and its protected evidence bundle remain authoritative.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


REQUIRED_MANUAL_RELEASE_IDS = tuple(f"MR-{number:02d}" for number in range(1, 10))
REQUIRED_APPROVALS = {
    "test_lead": "PASS",
    "field_operator": "PASS",
    "independent_reviewer": "APPROVED",
    "site_safety_contact": "APPROVED",
}
REQUIRED_BOOLEAN_CONTROLS = (
    "automated_suite_passed",
    "evidence_index_reviewed",
    "source_tree_clean",
    "phase3_adapter_read_only_scoped",
    "authorization_reference_present",
)
REQUIRED_TOP_LEVEL_FIELDS = frozenset({
    "schema_version",
    "campaign_id",
    "evidence_mode",
    "manual_release_checks",
    "approvals",
    *REQUIRED_BOOLEAN_CONTROLS,
    "unresolved_deviations",
})
_CAMPAIGN_ID = re.compile(r"AGQ-P2E-FIELD-[A-Z0-9][A-Z0-9._-]{0,79}")


def _campaign_hash(campaign_id: str) -> str:
    return hashlib.sha256(campaign_id.encode("utf-8")).hexdigest()


def _empty_summary(error: str) -> dict[str, Any]:
    return {
        "record_valid": False,
        "accepted": False,
        "decision": "BLOCKED",
        "campaign_ref_sha256": None,
        "evidence_mode": "unspecified",
        "manual_release_counts": {
            "pass": 0,
            "blocked": 0,
            "invalid": 0,
            "missing": len(REQUIRED_MANUAL_RELEASE_IDS),
        },
        "approval_count": 0,
        "required_approval_count": len(REQUIRED_APPROVALS),
        "automated_suite_passed": False,
        "evidence_index_reviewed": False,
        "source_tree_clean": False,
        "phase3_adapter_read_only_scoped": False,
        "authorization_reference_present": False,
        "unresolved_deviations": None,
        "errors": [error],
    }


def validate_field_release(record: Any) -> dict[str, Any]:
    """Return a non-sensitive, fail-closed post-field release summary."""
    if record is None:
        return _empty_summary("Private field-release summary is missing.")
    if not isinstance(record, Mapping):
        return _empty_summary("Private field-release summary must be a JSON object.")

    errors: list[str] = []
    supplied_fields = {str(field) for field in record}
    missing_fields = sorted(REQUIRED_TOP_LEVEL_FIELDS - supplied_fields)
    unknown_fields = sorted(supplied_fields - REQUIRED_TOP_LEVEL_FIELDS)
    if missing_fields:
        errors.append(f"Missing top-level fields: {', '.join(missing_fields)}.")
    if unknown_fields:
        errors.append(f"Unknown top-level fields: {', '.join(unknown_fields)}.")

    schema_version = record.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != 1:
        errors.append("schema_version must be 1.")

    campaign_id = record.get("campaign_id")
    if isinstance(campaign_id, str) and _CAMPAIGN_ID.fullmatch(campaign_id):
        campaign_ref = _campaign_hash(campaign_id)
    else:
        campaign_ref = None
        errors.append("campaign_id does not match the required AgroQ format.")

    evidence_mode = record.get("evidence_mode")
    if evidence_mode not in {"field", "simulation"}:
        errors.append("evidence_mode must be field or simulation.")
        normalized_mode = "unspecified"
    else:
        normalized_mode = evidence_mode

    checks = record.get("manual_release_checks")
    check_values = checks if isinstance(checks, Mapping) else {}
    if not isinstance(checks, Mapping):
        errors.append("manual_release_checks must be an object.")
    required_checks = set(REQUIRED_MANUAL_RELEASE_IDS)
    supplied_checks = {str(check_id) for check_id in check_values}
    missing_checks = sorted(required_checks - supplied_checks)
    unknown_checks = sorted(supplied_checks - required_checks)
    if missing_checks:
        errors.append(
            f"Missing manual release check IDs: {', '.join(missing_checks)}."
        )
    if unknown_checks:
        errors.append(
            f"Unknown manual release check IDs: {', '.join(unknown_checks)}."
        )

    normalized_checks: dict[str, str] = {}
    invalid_checks = 0
    for check_id in REQUIRED_MANUAL_RELEASE_IDS:
        if check_id not in check_values:
            continue
        status = check_values[check_id]
        if status not in {"PASS", "BLOCKED"}:
            invalid_checks += 1
            errors.append(f"Invalid status for {check_id}.")
            continue
        normalized_checks[check_id] = status
    manual_counts = {
        "pass": sum(status == "PASS" for status in normalized_checks.values()),
        "blocked": sum(status == "BLOCKED" for status in normalized_checks.values()),
        "invalid": invalid_checks,
        "missing": len(missing_checks),
    }

    approvals = record.get("approvals")
    approval_values = approvals if isinstance(approvals, Mapping) else {}
    if not isinstance(approvals, Mapping):
        errors.append("approvals must be an object.")
    required_roles = set(REQUIRED_APPROVALS)
    supplied_roles = {str(role) for role in approval_values}
    missing_roles = sorted(required_roles - supplied_roles)
    unknown_roles = sorted(supplied_roles - required_roles)
    if missing_roles:
        errors.append(f"Missing approval roles: {', '.join(missing_roles)}.")
    if unknown_roles:
        errors.append(f"Unknown approval roles: {', '.join(unknown_roles)}.")

    approval_count = 0
    for role, required_decision in REQUIRED_APPROVALS.items():
        if role not in approval_values:
            continue
        decision = approval_values[role]
        if decision not in {required_decision, "BLOCKED"}:
            errors.append(f"Invalid decision for approval role {role}.")
            continue
        if decision == required_decision:
            approval_count += 1

    boolean_controls: dict[str, bool] = {}
    for field in REQUIRED_BOOLEAN_CONTROLS:
        value = record.get(field)
        if not isinstance(value, bool):
            errors.append(f"{field} must be true or false.")
            boolean_controls[field] = False
        else:
            boolean_controls[field] = value

    unresolved = record.get("unresolved_deviations")
    if isinstance(unresolved, bool) or not isinstance(unresolved, int) or unresolved < 0:
        errors.append("unresolved_deviations must be a non-negative integer.")
        unresolved_count = None
    else:
        unresolved_count = unresolved

    record_valid = not errors
    accepted = bool(
        record_valid
        and normalized_mode == "field"
        and manual_counts["pass"] == len(REQUIRED_MANUAL_RELEASE_IDS)
        and manual_counts["blocked"] == 0
        and approval_count == len(REQUIRED_APPROVALS)
        and all(boolean_controls.values())
        and unresolved_count == 0
    )
    return {
        "record_valid": record_valid,
        "accepted": accepted,
        "decision": "APPROVED" if accepted else "BLOCKED",
        "campaign_ref_sha256": campaign_ref,
        "evidence_mode": normalized_mode,
        "manual_release_counts": manual_counts,
        "approval_count": approval_count,
        "required_approval_count": len(REQUIRED_APPROVALS),
        **boolean_controls,
        "unresolved_deviations": unresolved_count,
        "errors": errors,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty_summary("Private field-release summary is missing.")
    except json.JSONDecodeError:
        return _empty_summary("Private field-release summary is not valid JSON.")
    except OSError:
        return _empty_summary("Private field-release summary could not be read.")
    return validate_field_release(record)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a private Phase 2E post-field release summary."
    )
    parser.add_argument("--input", required=True, help="Path to the private field-release JSON file")
    parser.add_argument("--output", help="Optional path for the sanitized JSON summary")
    args = parser.parse_args()

    summary = load_and_validate(Path(args.input))
    rendered = json.dumps(summary, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
