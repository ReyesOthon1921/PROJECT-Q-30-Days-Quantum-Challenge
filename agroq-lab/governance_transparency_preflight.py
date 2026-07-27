import argparse
import json
from pathlib import Path


REQUIRED_FILES = (
    "agroq-lab/governance_transparency_registry.json",
    "agroq-lab/docs/Q23_Q25_GOVERNANCE_AI_AND_CALIFORNIA_NOTICES.md",
    "agroq-lab/investor-ui/src/components/GovernanceTransparencyPage.jsx",
    "agroq-lab/investor-ui/src/governance_transparency.css",
)


def validate(repo_root: Path) -> dict:
    missing = [item for item in REQUIRED_FILES if not (repo_root / item).is_file()]
    if missing:
        raise ValueError(f"Missing Q23-Q25 files: {', '.join(missing)}")

    registry = json.loads(
        (repo_root / "agroq-lab/governance_transparency_registry.json").read_text(
            encoding="utf-8"
        )
    )
    leaders = {item["name"]: item for item in registry["leadership"]}
    if leaders["Edith Ortiz"]["title"] != "Co-Founder and Operations Lead":
        raise ValueError("Edith Ortiz role is not the approved public title.")
    if registry["product"]["automatic_field_actuation"]:
        raise ValueError("Automatic field actuation must remain disabled.")
    if registry["ai_and_media"]["validated_agricultural_performance_claim"]:
        raise ValueError("Validated agricultural performance must not be claimed.")
    if registry["ai_and_media"]["quantum_advantage_claim"]:
        raise ValueError("Quantum advantage must not be claimed.")
    program = registry["founding_grower_program"]
    if program["automatic_renewal_active"]:
        raise ValueError("Automatic renewal must remain inactive.")
    expected = [500, 800, 1000]
    observed = [
        item.get("proposed_first_year_usd", item.get("planned_first_year_usd"))
        for item in program["tiers"]
    ]
    if observed != expected or program["planned_year_two_annual_usd"] != 1500:
        raise ValueError("Founding Grower preliminary pricing drift detected.")

    app_text = (repo_root / "agroq-lab/investor-ui/src/App.jsx").read_text(
        encoding="utf-8"
    )
    for marker in (
        "GovernanceTransparencyPage",
        'id: "governance"',
        "Edith Ortiz",
        "Co-Founder · Operations Lead",
    ):
        if marker not in app_text:
            raise ValueError(f"App integration marker missing: {marker}")

    return {
        "schema_version": registry["schema_version"],
        "status": "passed",
        "leadership_count": len(registry["leadership"]),
        "automatic_field_actuation": False,
        "automatic_renewal_active": False,
        "ai_assistance_disclosed": True,
        "validated_performance_claim": False,
        "quantum_advantage_claim": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--output",
        default="agroq-lab/results/governance_transparency/code_readiness.json",
    )
    args = parser.parse_args()
    result = validate(Path(args.repo_root).resolve())
    output = Path(args.repo_root).resolve() / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Q23-Q25 governance transparency preflight passed: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
