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

Then generate the evidence report:

```bat
python scripts\phase2e_acceptance.py
```

A blocked result is expected until the real field outage, backup, device, and
manual-workflow evidence exists. Never modify the database merely to force a pass.

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
manual checks above are signed by the responsible operator, and the Phase 2E
commit has a clean working tree. The first Phase 3 adapter remains read-only:
raw payload preservation, normalization, comparison with manual measurements,
and failure isolation are required before any broader integration.
