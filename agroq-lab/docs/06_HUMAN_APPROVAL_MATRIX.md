# Human Approval Matrix

| Proposed action | System may recommend | System may execute in MVP | Required reviewer |
|---|---:|---:|---|
| Collect another measurement | Yes | No | Field lead |
| Create inspection task | Yes | Yes, as a task only | Field lead reviews queue |
| Change sensor sampling rate | Yes | No | Electrical/software lead |
| Open irrigation valve | Yes | No | Authorized field operator |
| Apply fertilizer or treatment | Yes | No | Agronomy/biology reviewer |
| Release beneficial organisms | Yes | No | Biology/ecology reviewer |
| Move mobile equipment | Yes | No | Authorized operator |
| Reject suspect data | Flag only | No deletion | Research lead |
| Retrain model | Yes | No production promotion | ML/research lead |
| Run quantum experiment | Yes | Research sandbox only | Quantum/research lead |

## Approval record

Every decision stores:

```text
recommendation_id
reviewer
decision
decision_notes
edits
timestamp
required_follow_up
outcome_due
```
