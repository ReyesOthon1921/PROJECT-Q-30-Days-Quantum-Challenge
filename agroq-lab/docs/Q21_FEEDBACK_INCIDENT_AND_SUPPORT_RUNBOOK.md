# Q21 — Feedback, Incident, and Support Runbook

## Feedback

The assigned participant or an operations user may submit feedback. The
original category, rating, description, context, evidence reference, submitter,
and timestamp are immutable. Triage and resolution are stored as separate
review records so the original report remains intact.

## Incident response

Every incident records severity, category, impact, immediate manual action,
evidence, reporter, and timestamp. Status changes are append-only events.

1. Preserve the original report and related evidence.
2. Record the immediate manual action.
3. Triage the incident.
4. Record containment, resolution, and closure as new events.
5. Attach evidence before marking an incident resolved or closed.

High and critical incidents automatically change an active pilot to `paused`.
This is a software safety stop, not a field action. The system does not operate
equipment, apply treatments, or suppress manual work.

## Escalation

- Low: normal operations review.
- Medium: prioritized human review.
- High: pilot pause and administrator review.
- Critical: pilot pause, evidence preservation, and administrator review.

Release-review recommendations remain blocked while a high or critical
incident is unresolved.
