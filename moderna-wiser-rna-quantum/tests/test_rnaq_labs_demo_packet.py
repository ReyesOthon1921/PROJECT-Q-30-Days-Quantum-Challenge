from src.reports.rnaq_labs_demo_packet import (
    build_conflict_edges,
    build_demo_packet,
    generate_candidate_pairs,
    generate_candidate_stems,
    normalize_sequence,
)


def test_normalize_sequence_accepts_dna_t_as_rna_u():
    assert normalize_sequence("gggAAAtcc") == "GGGAAAUCC"


def test_candidate_generation_returns_pairs_and_stems_for_demo_sequence():
    seq = normalize_sequence("GGGAAAUCC")
    pairs = generate_candidate_pairs(seq)
    stems = generate_candidate_stems(pairs)
    assert len(pairs) >= 3
    assert len(stems) >= 1


def test_conflict_edges_are_well_formed():
    seq = normalize_sequence("GGGAAAUCC")
    stems = generate_candidate_stems(generate_candidate_pairs(seq))
    edges = build_conflict_edges(stems)
    assert all(a < b for a, b in edges)


def test_demo_packet_has_required_mvp_fields():
    result = build_demo_packet("GGGAAAUCC", audience="challenge", label="test")
    assert result.label == "test"
    assert result.sequence == "GGGAAAUCC"
    assert result.qubo_variable_count == result.candidate_stem_count
    assert result.graph_risk_label in {"Low graph risk", "Medium graph risk", "High graph risk"}
    assert "quantum advantage" in result.safe_claim.lower()


def test_invalid_sequence_raises_value_error():
    try:
        build_demo_packet("ABCXYZ")
    except ValueError as exc:
        assert "Invalid RNA bases" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid sequence")
