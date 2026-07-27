# Q20–Q22 Architecture and Boundaries

## Data flow

```text
Q17 accepted staging candidate
        +
Q18 approved pilot discovery
        |
        v
Q20 enrollment -> onboarding evidence -> acknowledgments -> human activation
        |
        v
Q21 immutable feedback + append-only incident events
        |
        v
Q22 immutable metrics -> blocker evaluation -> human exit decision
```

## Roles

- Viewer or assigned participant: read pilot information and submit their own
  acknowledgments, feedback, and incident reports.
- Researcher: complete onboarding checks, review feedback and incidents, and
  record evidence-backed metrics.
- Administrator: create enrollments, activate or reactivate pilots, and record
  exit decisions.

## Non-negotiable boundaries

- Manual workflows are never removed.
- Raw feedback, incidents, acknowledgments, metrics, and exit decisions are
  immutable.
- Serious incidents pause the software pilot for human review.
- No recommendation directly controls field equipment.
- No unsupported quantum, agricultural, security, or performance claim is
  approved by these phases.
- No API in Q20–Q22 deploys or promotes production.
