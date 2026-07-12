from __future__ import annotations

import math

from src.evaluation.qubo_graph_laplacian_diagnostics import (
    analyze_qubo_interaction_graph,
    connected_components,
    normalize_edges,
)


def test_normalize_edges_removes_duplicates_and_self_loops():
    edges = [(0, 1, 1.0), (1, 0, 2.0), (2, 2, 5.0), (9, 10, 1.0)]
    normalized = normalize_edges(3, edges)

    assert normalized == [(0, 1, 3.0)]


def test_empty_graph_has_no_edges_and_multiple_components():
    result = analyze_qubo_interaction_graph(
        sequence_id="empty",
        variable_count=3,
        edges=[],
    )

    assert result.variable_count == 3
    assert result.edge_count == 0
    assert result.graph_density == 0.0
    assert result.connected_component_count == 3
    assert result.analysis_status == "no_interaction_edges_detected"


def test_path_graph_diagnostics_are_reasonable():
    result = analyze_qubo_interaction_graph(
        sequence_id="path",
        variable_count=3,
        edges=[(0, 1, 1.0), (1, 2, 1.0)],
    )

    assert result.variable_count == 3
    assert result.edge_count == 2
    assert math.isclose(result.graph_density, 2 / 3, rel_tol=1e-6)
    assert result.max_degree == 2
    assert result.connected_component_count == 1
    assert result.laplacian_lambda_2 is None or result.laplacian_lambda_2 >= 0.0
    assert result.spectral_risk_score > 0.0


def test_complete_graph_density_is_one():
    edges = [
        (0, 1, 1.0),
        (0, 2, 1.0),
        (0, 3, 1.0),
        (1, 2, 1.0),
        (1, 3, 1.0),
        (2, 3, 1.0),
    ]

    result = analyze_qubo_interaction_graph(
        sequence_id="complete",
        variable_count=4,
        edges=edges,
    )

    assert result.edge_count == 6
    assert math.isclose(result.graph_density, 1.0)
    assert result.max_degree == 3
    assert result.hub_degree_ratio == 1.0


def test_connected_components_detects_two_components():
    components = connected_components(
        variable_count=5,
        edges=[(0, 1, 1.0), (1, 2, 1.0), (3, 4, 1.0)],
    )

    assert components == [[0, 1, 2], [3, 4]]
