# Data Model

## Core entities

| Entity | Purpose |
|---|---|
| Site | Physical research location |
| Plot | Experimental unit |
| Asset | Tool, sensor, gateway, structure, or equipment |
| Observation | Manual, sensor, laboratory, or imported measurement |
| ManualTask | Human work assignment and completion record |
| Experiment | Hypothesis, treatments, controls, and status |
| Sample | Physical specimen and custody trail |
| Recommendation | Proposed action from a rule, model, or solver |
| Decision | Human approval, rejection, or edit |
| Action | Work actually performed |
| Outcome | Measurement after the action |
| ModelVersion | Training data, code, metrics, and deployment status |
| OptimizationRun | Objective, constraints, solver, seed, and result |
| GraphVersion | Nodes, edges, construction method, and Laplacian settings |
| AuditEvent | Who changed what and when |

## Observation provenance

```text
observation_id
plot_id
asset_id
property
raw_value
corrected_value
unit
source_type
method
calibration_version
quality_flag
uncertainty
observed_at
recorded_at
operator
notes
```

## Truth labels for computation

- `rule`
- `classical_statistics`
- `machine_learning`
- `deep_learning`
- `quantum_inspired`
- `quantum_simulator`
- `quantum_hardware`
- `quantum_sensor`
