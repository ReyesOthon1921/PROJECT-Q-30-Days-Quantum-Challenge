# Q22 — Pilot Evidence and Exit Decision

## Evidence metrics

Each metric observation contains a unique ID, metric code and name, baseline,
target, observed value, unit, direction, evidence reference, SHA-256 digest,
limitations, recorder, and timestamp. Metric observations are immutable.

## Release-review gate

`recommend_release_review` requires:

- an activated pilot;
- at least three distinct evidence-backed metrics;
- at least one participant feedback record;
- a completed post-pilot interview; and
- no unresolved high or critical incident.

The decision is immutable and records the blocker snapshot evaluated at the
time of review.

## Decision meanings

- `continue` — keep the current controlled scope.
- `extend` — allow more time without expanding scope automatically.
- `pause` — stop pilot activity pending human review.
- `complete` — end the controlled pilot.
- `stop` — withdraw the enrollment.
- `recommend_release_review` — recommend a separate release review.

No Q22 decision deploys staging, promotes production, merges a pull request, or
authorizes physical field integration.

## Evidence export

The ZIP contains the enrollment record, feedback, incident history, metrics,
decisions, relevant approved or restricted claims, explicit boundaries,
`manifest.json`, and `SHA256SUMS.txt`. ZIP entry ordering and timestamps are
fixed for reproducible packaging of the same snapshot.
