from pathlib import Path

from controlled_beta_preflight import run_preflight


def test_controlled_beta_preflight_passes_complete_structure(tmp_path):
    repo = tmp_path
    agroq = repo / "agroq-lab"
    docs = agroq / "docs"
    investor = agroq / "investor-ui" / "src"
    components = investor / "components"
    docs.mkdir(parents=True)
    components.mkdir(parents=True)

    source_root = Path(__file__).resolve().parents[1]
    for name in (
        "access_schema.sql",
        "controlled_beta_schema.sql",
        "controlled_beta.py",
        "controlled_beta_preflight.py",
        "staging_acceptance_cli.py",
    ):
        (agroq / name).write_text(
            (source_root / name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    for name in (
        "Q17_STAGING_ACCEPTANCE_RUNBOOK.md",
        "Q17_RENDER_STAGING_BLUEPRINT.md",
        "Q18_USER_INTERVIEW_SCRIPT.md",
        "Q18_PILOT_DISCOVERY_WORKSHEET.md",
        "Q18_INVITATION_AND_ACCESS_POLICY.md",
        "Q19_CLAIMS_REGISTER_POLICY.md",
        "Q19_DEMO_AND_YC_EVIDENCE.md",
        "CONTROLLED_BETA_ARCHITECTURE_AND_LIMITATIONS.md",
        "CONTROLLED_BETA_PULL_REQUEST.md",
    ):
        (docs / name).write_text(name, encoding="utf-8")

    (components / "ControlledBetaWorkspace.jsx").write_text(
        "export default function ControlledBetaWorkspace(){return null;}",
        encoding="utf-8",
    )
    (investor / "controlled_beta.css").write_text(
        ".q17-stack{}",
        encoding="utf-8",
    )
    staging = agroq / "deployment" / "staging"
    staging.mkdir(parents=True)
    (staging / "frontend.Dockerfile").write_text(
        "FROM nginx:alpine",
        encoding="utf-8",
    )
    (staging / "nginx.conf.template").write_text(
        "server {}",
        encoding="utf-8",
    )
    (repo / "render.staging.yaml").write_text(
        "services: []",
        encoding="utf-8",
    )

    report = run_preflight(repo)
    assert report["passed"] is True
