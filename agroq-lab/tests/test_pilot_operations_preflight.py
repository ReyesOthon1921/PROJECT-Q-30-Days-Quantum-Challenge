from pathlib import Path

from pilot_operations_preflight import run_preflight


def test_q20_q22_preflight_passes_repository_structure():
    repo_root = Path(__file__).resolve().parents[2]
    report = run_preflight(repo_root)
    assert report["passed"] is True
    assert report["schema_version"] == "AGROQ-PILOT-OPERATIONS-1.0-PREFLIGHT"
    assert all(check["passed"] for check in report["checks"])
    assert any("No remote deployment" in item for item in report["boundaries"])
