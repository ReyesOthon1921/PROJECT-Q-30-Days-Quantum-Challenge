from __future__ import annotations

from src.evaluation.vienna_preflight import build_preflight_report, format_preflight_report


def test_preflight_report_contains_status_keys():
    report = build_preflight_report()
    assert "rnafold_cli_available" in report
    assert "viennarna_python_available" in report
    assert "vienna_reference_ready" in report


def test_format_preflight_report_is_readable():
    report = {
        "rnafold_executable": "RNAfold",
        "rnafold_cli_available": False,
        "viennarna_python_available": False,
        "vienna_reference_ready": False,
        "recommended_action": "Install ViennaRNA.",
    }
    text = format_preflight_report(report)
    assert "ViennaRNA preflight check" in text
    assert "RNAfold CLI available: no" in text
    assert "Vienna reference status: not ready" in text
