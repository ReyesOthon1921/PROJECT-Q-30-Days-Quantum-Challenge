# Graph Laplacian Diagnostics for RNA-QUBO Interaction Graphs

## Purpose

This document connects the updated mathematical discussion and Graph Laplacian notes to the implemented RNA-QUBO project.

Candidate stems are treated as QUBO variables. Nonzero quadratic QUBO interactions are treated as graph edges. The Graph Laplacian provides a diagnostic layer for optimization difficulty, hub variables, spectral structure, and graph-aware QRAO compression risk.

This layer is an interpretability and readiness tool. It does not claim improved biological accuracy, quantum advantage, or validated compression improvement.

## Metrics

- `variable_count`: number of QUBO variables detected for the run.
- `edge_count`: number of nonzero quadratic interaction edges detected.
- `graph_density`: interaction density of the QUBO graph.
- `max_degree`: largest number of conflicts/interactions connected to one variable.
- `degree_variance`: hub concentration signal.
- `laplacian_lambda_2`: second-smallest Laplacian eigenvalue when available.
- `fiedler_balance`: balance of the Fiedler split when available.
- `spectral_risk_score`: project-specific diagnostic score for graph-structure difficulty.

## Output Table

| sequence_id | variable_count | edge_count | graph_density | max_degree | laplacian_lambda_2 | spectral_risk_score | analysis_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| seq_001 | 4 | 6 | 1.0 | 3 | 40.0 | 100.0 | high_graph_structure_risk |
| seq_002 | 2 | 1 | 1.0 | 1 | 20.0 | 100.0 | high_graph_structure_risk |
| seq_003 | 4 | 6 | 1.0 | 3 | 40.0 | 100.0 | high_graph_structure_risk |
| seq_004 | 1 | 0 | 0.0 | 0 | None | 15.0 | no_interaction_edges_detected |
| seq_005 | 2 | 1 | 1.0 | 1 | 20.0 | 100.0 | high_graph_structure_risk |
| seq_006 | 5 | 10 | 1.0 | 4 | 54.15044557 | 100.0 | high_graph_structure_risk |
| seq_007 | 3 | 3 | 1.0 | 2 | 38.0 | 100.0 | high_graph_structure_risk |
| seq_008 | 5 | 10 | 1.0 | 4 | 56.63930811 | 100.0 | high_graph_structure_risk |
| seq_009 | 5 | 10 | 1.0 | 4 | 50.0 | 100.0 | high_graph_structure_risk |
| seq_010 | 3 | 3 | 1.0 | 2 | 30.0 | 100.0 | high_graph_structure_risk |
| seq_011 | 5 | 10 | 1.0 | 4 | 50.0 | 100.0 | high_graph_structure_risk |
| seq_012 | 3 | 3 | 1.0 | 2 | 30.0 | 100.0 | high_graph_structure_risk |

## Safe Claim Boundary

- This is a graph-diagnostic layer, not a new RNA thermodynamic model.
- QUBO graph structure can explain optimization and compression risk, but it does not prove quantum advantage.
- Graph-aware QRAO packing should be evaluated with rounding, feasibility, and solution-quality metrics before being treated as a central claim.
