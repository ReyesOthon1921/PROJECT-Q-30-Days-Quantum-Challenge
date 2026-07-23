"""Validate a private Phase 2E readiness summary without exposing identities.

The machine-readable record is a secondary control. The signed private copies
of Documents 13 and 14 remain the authoritative human records. This validator
does not start a field test and cannot authorize Phase 3 physical integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping


REQUIRED_READINESS_IDS = tuple(f"P2E-RD-{number:02d}" for number in range(1, 16))
REQUIRED_PREFLIGHT_IDS = tuple(f"PF-{number:02d}" for number in range(1, 16))
REQUIRED_APPROVALS = {
    "test_lead": "READY",
    "field_operator": "ACCEPTED",
    "independent_reviewer": "AUTHORIZED",
    "site_safety_contact": "APPROVED",
    "adult_lab_supervisor": "APPROVED",
    "backup_recovery_witness": "ACKNOWLEDGED",
}
REQUIRED_TOP_LEVEL_FIELDS = frozenset({
    "schema_version",
    "assessment_id",
    "campaign_id",
    "readiness_checks",
    "preflight_checks",
    "approvals",
    "separation_of_duties_confirmed",
    "unresolved_deviations",
})

_ASSESSMENT_ID = re.compile(r"AGQ-P2E-RD-[A-Z0-9][A-Z0-9._-]{0,79}")
_CAMPAIGN_ID = re.compile(r"AGQ-P2E-FIELD-[A-Z0-9][A-Z0-9._-]{0,79}")


def _empty_summary(error: str) -> dict[str, Any]:
    return {
        "record_valid": False,
        "ready": False,
        "decision": "NO-GO",
        "campaign_ref_sha256": None,
        "readiness_counts": {
            "pass": 0,
            "fail": 0,
            "blocked": 0,
            "invalid": 0,
            "missing": len(REQUIRED_READINESS_IDS),
        },
        "preflight_counts": {
            "pass": 0,
            "blocked": 0,
            "invalid": 0,
            "missing": len(REQUIRED_PREFLIGHT_IDS),
        },
        "approval_count": 0,
        "required_approval_count": len(REQUIRED_APPROVALS),
        "separation_of_duties_confirmed": False,
        "unresolved_deviations": None,
        "errors": [error],
    }


def _status_counts(
    value: Any,
    required_ids: tuple[str, ...],
    allowed_statuses: frozenset[str],
    label: str,
    errors: list[str],
) -> tuple[dict[str, int], dict[str, str]]:
    statuses = value if isinstance(value, Mapping) else {}
    if not isinstance(value, Mapping):
        errors.append(f"{label.capitalize()} checks must be an object.")

    required = set(required_ids)
    supplied = {str(check_id) for check_id in statuses}
    missing = sorted(required - supplied)
    unknown = sorted(supplied - required)
    if missing:
        errors.append(f"Missing {label} check IDs: {', '.join(missing)}.")
    if unknown:
        errors.append(f"Unknown {label} check IDs: {', '.join(unknown)}.")

    normalized: dict[str, str] = {}
    invalid = 0
    for check_id in required_ids:
        if check_id not in statuses:
            continue
        status = statuses[check_id]
        if not isinstance(status, str) or status not in allowed_statuses:
            invalid += 1
            errors.append(f"Invalid status for {check_id}.")
            continue
        normalized[check_id] = status

    counts = {
        "pass": sum(status == "PASS" for status in normalized.values()),
        "blocked": sum(status == "BLOCKED" for status in normalized.values()),
        "invalid": invalid,
        "missing": len(missing),
    }
    if "FAIL" in allowed_statuses:
        counts = {
            "pass": counts["pass"],
            "fail": sum(status == "FAIL" for status in normalized.values()),
            "blocked": counts["blocked"],
            "invalid": counts["invalid"],
            "missing": counts["missing"],
        }
    return counts, normalized


def validate_readiness(record: Any) -> dict[str, Any]:
    """Return a non-sensitive, fail-closed readiness summary."""
    if record is None:
        return _empty_summary("Private readiness summary is missing.")
    if not isinstance(record, Mapping):
        return _empty_summary("Private readiness summary must be a JSON object.")

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

    assessment_id = record.get("assessment_id")
    if not isinstance(assessment_id, str) or not _ASSESSMENT_ID.fullmatch(assessment_id):
        errors.append("assessment_id does not match the required AgroQ format.")

    campaign_id = record.get("campaign_id")
    if not isinstance(campaign_id, str) or not _CAMPAIGN_ID.fullmatch(campaign_id):
        campaign_ref = None
        errors.append("campaign_id does not match the required AgroQ format.")
    else:
        campaign_ref = hashlib.sha256(campaign_id.encode("utf-8")).hexdigest()

    readiness_counts, _ = _status_counts(
        record.get("readiness_checks"),
        REQUIRED_READINESS_IDS,
        frozenset({"PASS", "FAIL", "BLOCKED"}),
        "readiness",
        errors,
    )
    preflight_counts, _ = _status_counts(
        record.get("preflight_checks"),
        REQUIRED_PREFLIGHT_IDS,
        frozenset({"PASS", "BLOCKED"}),
        "preflight",
        errors,
    )

    approvals = record.get("approvals")
    approval_values = approvals if isinstance(approvals, Mapping) else {}
    if not isinstance(approvals, Mapping):
        errors.append("approvals must be an object.")
    supplied_roles = {str(role) for role in approval_values}
    required_roles = set(REQUIRED_APPROVALS)
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

    separation = record.get("separation_of_duties_confirmed")
    if not isinstance(separation, bool):
        errors.append("separation_of_duties_confirmed must be true or false.")
        separation_confirmed = False
    else:
        separation_confirmed = separation

    unresolved = record.get("unresolved_deviations")
    if isinstance(unresolved, bool) or not isinstance(unresolved, int) or unresolved < 0:
        errors.append("unresolved_deviations must be a non-negative integer.")
        unresolved_count = None
    else:
        unresolved_count = unresolved

    record_valid = not errors
    ready = bool(
        record_valid
        and readiness_counts["pass"] == len(REQUIRED_READINESS_IDS)
        and readiness_counts["fail"] == 0
        and readiness_counts["blocked"] == 0
        and preflight_counts["pass"] == len(REQUIRED_PREFLIGHT_IDS)
        and preflight_counts["blocked"] == 0
        and approval_count == len(REQUIRED_APPROVALS)
        and separation_confirmed
        and unresolved_count == 0
    )
    return {
        "record_valid": record_valid,
        "ready": ready,
        "decision": "GO" if ready else "NO-GO",
        "campaign_ref_sha256": campaign_ref,
        "readiness_counts": readiness_counts,
        "preflight_counts": preflight_counts,
        "approval_count": approval_count,
        "required_approval_count": len(REQUIRED_APPROVALS),
        "separation_of_duties_confirmed": separation_confirmed,
        "unresolved_deviations": unresolved_count,
        "errors": errors,
    }


def load_and_validate(path: Path) -> dict[str, Any]:
    """Load a private JSON record and return only its sanitized summary."""
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _empty_summary("Private readiness summary is missing.")
    except json.JSONDecodeError:
        return _empty_summary("Private readiness summary is not valid JSON.")
    except OSError:
        return _empty_summary("Private readiness summary could not be read.")
    return validate_readiness(record)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a private Phase 2E readiness summary without exposing identities."
    )
    parser.add_argument("--input", required=True, help="Path to the private readiness JSON file")
    parser.add_argument("--output", help="Optional path for the sanitized JSON summary")
    args = parser.parse_args()

    summary = load_and_validate(Path(args.input))
    rendered = json.dumps(summary, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if summary["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
