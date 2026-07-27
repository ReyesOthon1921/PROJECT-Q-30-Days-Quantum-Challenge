from pathlib import Path


def test_misbahul_acknowledgment_role_and_boundaries():
    root = Path(__file__).resolve().parents[1]
    workspace = (
        root
        / "investor-ui"
        / "src"
        / "components"
        / "QuantumRegistryWorkspace.jsx"
    ).read_text(encoding="utf-8")
    documentation = (
        root / "docs" / "RESEARCH_MENTORS_AND_COLLABORATORS.md"
    ).read_text(encoding="utf-8")

    for text in (workspace, documentation):
        assert "Misbahul Islam" in text
        assert "Research Mentor &amp; Publication Collaborator" in text or (
            "Research Mentor & Publication Collaborator" in text
        )
        assert "BLAST" in text
        assert "RCSB PDB" in text
        assert "co-founder" in text
        assert "principal investigator" in text
        assert "authorship" in text

    assert "Research Mentors &amp; Collaborators" in workspace
    assert "Othon Reyes Jr. remains responsible" in workspace or (
        "Othon Reyes Jr. continues developing" in workspace
    )
