# Q20 — Controlled Pilot Activation

## Purpose

Q20 converts an approved discovery record and an accepted staging candidate
into a named, auditable pilot enrollment. It does not create a public signup
path and does not deploy software.

## Required activation gates

The administrator may activate an enrollment only when:

1. The Q17 staging candidate is accepted.
2. The Q18 pilot discovery record is approved.
3. An active participant account and support owner are assigned.
4. All six required onboarding checks contain evidence.
5. Data-handling, human-control, and research-limitations acknowledgments are
   accepted and preserved as immutable records.
6. The administrator records a human-readable activation reason.

## Operating boundary

- Manual entry and manual correction workflows remain available.
- Automated equipment control remains prohibited.
- A high or critical incident pauses an active pilot.
- Reactivation requires an administrator decision.
- Activation does not authorize production promotion.

## Operator sequence

1. Create the enrollment from an approved pilot and accepted staging candidate.
2. Assign the participant user, cohort, controlled scope, exclusion scope, and
   support owner.
3. Complete onboarding checks with evidence references.
4. Capture the three required acknowledgments.
5. Review the blocker list.
6. Record the activation decision.
