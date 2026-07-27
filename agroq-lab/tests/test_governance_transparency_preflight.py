import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_preflight():
    path = ROOT / "agroq-lab/governance_transparency_preflight.py"
    spec = importlib.util.spec_from_file_location("governance_preflight", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_registry_preserves_founders_and_boundaries():
    registry = json.loads(
        (ROOT / "agroq-lab/governance_transparency_registry.json").read_text()
    )
    leaders = {item["name"]: item["title"] for item in registry["leadership"]}
    assert leaders["Othon Reyes Jr."] == "Founder, CEO, and Technical Lead"
    assert leaders["Edith Ortiz"] == "Co-Founder and Operations Lead"
    assert registry["product"]["automatic_field_actuation"] is False
    assert registry["ai_and_media"]["quantum_advantage_claim"] is False


def test_founder_program_is_preliminary_and_not_automatic():
    registry = json.loads(
        (ROOT / "agroq-lab/governance_transparency_registry.json").read_text()
    )
    program = registry["founding_grower_program"]
    assert program["application_is_nonbinding"] is True
    assert program["payment_collected_through_application"] is False
    assert program["automatic_renewal_active"] is False
    assert program["planned_year_two_annual_usd"] == 1500


def test_preflight_passes():
    result = load_preflight().validate(ROOT)
    assert result["status"] == "passed"
    assert result["leadership_count"] == 2
