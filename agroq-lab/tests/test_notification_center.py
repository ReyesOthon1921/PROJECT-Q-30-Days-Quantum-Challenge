from __future__ import annotations

from notification_center import (
    REDACTED,
    audit_action_profile,
    sanitize_metadata,
)


def test_sensitive_values_are_redacted():
    result = sanitize_metadata(
        {
            "username": "example",
            "password": "never-store-this",
            "nested": {
                "pin": "12345678",
                "token": "secret-token",
                "ip": "127.0.0.1",
            },
        }
    )
    assert result["username"] == "example"
    assert result["password"] == REDACTED
    assert result["nested"]["pin"] == REDACTED
    assert result["nested"]["token"] == REDACTED
    assert result["nested"]["ip"] == "127.0.0.1"


def test_login_audit_mapping():
    profile = audit_action_profile("login")
    assert profile is not None
    assert profile["event_type"] == "login_success"


def test_password_audit_mapping_is_warning():
    profile = audit_action_profile("password_changed")
    assert profile is not None
    assert profile["severity"] == "warning"


def test_access_audit_mapping():
    profile = audit_action_profile("access_request_created")
    assert profile is not None
    assert profile["event_type"] == "access_activity"


def test_unrelated_audit_action_is_ignored():
    assert audit_action_profile("observation_created") is None
