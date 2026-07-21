# RNAQ Labs 3-Minute Demo Script

## 0:00–0:30 — Problem
RNA and biological optimization workflows can be difficult to validate, explain, and reproduce. The MVP focuses on making one sequence easy to test and explain.

## 0:30–1:10 — Input
Paste an RNA sequence or choose a sample sequence. The app validates the sequence and prepares it for candidate base-pair and stem generation.

## 1:10–1:50 — QUBO and graph structure
Candidate stems become QUBO variables. Stem conflicts become graph edges. This makes the optimization problem auditable and prepares the model for graph-aware compression analysis.

## 1:50–2:30 — Result
The demo reports candidate stems, QUBO variables, conflict edges, graph density, graph risk, and a recommended solver path.

## 2:30–3:00 — Close
The MVP is not claiming quantum advantage or biological deployment. It is a reproducible decision-intelligence workflow that helps decide what to validate next.
