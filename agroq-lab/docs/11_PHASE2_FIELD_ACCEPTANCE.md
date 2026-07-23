# Phase 2E Field Acceptance and Release Readiness

## Purpose

Phase 2E closes the local-gateway phase before physical sensors are introduced.
It records evidence and produces a human-reviewable release gate. It does not
connect sensors, ingest sensor payloads, or authorize automatic field actions.

## Required acceptance evidence

1. The complete automated test suite passes on the field computer.
2. LAN deployment configuration reports ready with debug disabled and a non-development secret.
3. At least one measured 24-hour outage test has passed.
4. At least one local backup has passed recovery verification.
5. At least one non-retired device has append-only health history.
6. A manual observation and its audit evidence remain available without external APIs.
7. JSON/CSV export is manually opened and inspected.
8. A second operator follows the README and independently starts the gateway.

## Acceptance run

Run the automated suite first:

```bat
python -m pytest -q
```

Then generate the preliminary technical evidence report. It must remain blocked
until the post-field release review is completed:

```bat
python scripts\phase2e_acceptance.py --evidence-mode field --readiness "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_readiness_private.json" --db "instance\agroq_phase2_field_validation.db"
```

A blocked result is expected until the real field outage, backup, device, and
manual-workflow evidence exists and the private readiness summary validates.
Never modify the database or readiness summary merely to force a pass.

## Private readiness-summary gate

The signed private copies of Documents 13 and 14 remain the authoritative human
records. The JSON summary is a machine-readable, non-sensitive secondary control.
It contains check results and role decisions only; do not add names, signatures,
addresses, credentials, IP information, or private paths.

Create the private file outside Git from the blocked-by-default example:

```bat
mkdir "%USERPROFILE%\Documents\AgroQ-Private\Phase2E"
copy /Y "config\phase2e_readiness_summary.example.json" "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_readiness_private.json"
```

Validate it separately:

```bat
python scripts\phase2e_readiness.py --input "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_readiness_private.json"
```

The validator returns `GO` only for 15 readiness passes, 15 Document 13
preflight passes, all six required positive role decisions, confirmed separation
of duties, zero unresolved deviations, and a valid schema. A valid `GO` summary
authorizes only the controlled Phase 2E field campaign; it does not authorize
Phase 3 physical integration.

After MR-01 through MR-09 and the final Document 12 approvals are genuinely
completed, create a separate private post-field summary:

```bat
copy /Y "config\phase2e_field_release.example.json" "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_field_release_private.json"
```

Validate it:

```bat
python scripts\phase2e_field_release.py --input "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_field_release_private.json"
```

Only then run the final combined release gate:

```bat
python scripts\phase2e_acceptance.py --evidence-mode field --readiness "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_readiness_private.json" --field-release "%USERPROFILE%\Documents\AgroQ-Private\Phase2E\phase2e_field_release_private.json" --db "instance\agroq_phase2_field_validation.db"
```

The preflight and post-field files must use the same campaign ID. The generated
public report retains only a SHA-256 campaign reference, counts, decisions, and
non-sensitive status information.

## Database migration decision

SQLite remains the Phase 2 release database because the current target is one
local field gateway, offline operation, simple recovery, and a small operator
team. PostgreSQL is deferred rather than rejected.

Reopen the migration decision when any two of these conditions occur:

- sustained concurrent writers cause lock contention;
- multiple gateways need a shared authoritative database;
- data volume or query latency misses a documented service target;
- centralized high-availability or managed replication becomes required;
- access-control or audit requirements exceed the local deployment model.

The migration must be a separate tested checkpoint with backup, rollback,
schema parity, export parity, and outage behavior verified before production use.

## Phase 3 entry gate

Phase 3 may start only after the generated report says `ready_for_phase3`, the
private manual records are signed by all required roles, the independent reviewer
approves the field evidence, and the Phase 2E commit has a clean working tree.
The first Phase 3 adapter remains read-only:
raw payload preservation, normalization, comparison with manual measurements,
and failure isolation are required before any broader integration.
