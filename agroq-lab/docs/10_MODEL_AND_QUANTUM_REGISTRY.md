# Model and Quantum Registry

## Model record

```text
model_id
name
purpose
computation_type
code_commit
training_dataset
validation_dataset
feature_schema
metrics
known limitations
approved use
deployment status
owner
created_at
```

## Required baseline

Every model has a baseline row:

| Advanced method | Minimum baseline |
|---|---|
| Deep image model | Simple image classifier or manual count |
| Temporal GNN | Persistence and standard forecasting |
| Reservoir model | Linear autoregression and classical reservoir |
| Bayesian experiment selection | Fixed or randomized design |
| QUBO/QAOA | Greedy plus exact/MILP where possible |
| Quantum kernel | Classical kernel with matched split |

## Quantum claim gate

Do not call a result quantum advantage unless:

1. computation used actual quantum hardware;
2. comparison used an appropriate strong classical method;
3. budgets and data were matched;
4. result was repeated;
5. uncertainty and failure cases were reported;
6. value was operationally meaningful.
