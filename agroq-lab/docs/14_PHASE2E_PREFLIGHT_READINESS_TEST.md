# AgroQ Phase 2E Preflight Readiness Test

Document status: Controlled readiness test

Applies to: AgroQ Phase 2E verified-field validation

Purpose: Test whether `docs/13_PHASE2E_FIELD_TEST_PREFLIGHT_RECORD.md` contains enough verified information and authorization to schedule the genuine 24-hour field test. This document does not start the field test and does not authorize physical Phase 3 integration.

## 1. Safety boundary

- Run this readiness test before any WAN interruption, physical sensor connection, electrical work, or field-data collection.
- Use only an approved, noncritical test location and approved equipment.
- An adult or qualified lab supervisor must approve and supervise any physical or network action.
- Do not test against school, employer, production, shared, or safety-critical networks.
- Do not use the simulation loader, simulation database, or generated simulation results as field evidence.
- Keep the completed private record, signatures, private addresses, credentials, IP addresses, and sensitive network paths outside the public GitHub repository.
- A missing, assumed, placeholder, or unverified value is a failure, not a pass.

## 2. Test result states

Use exactly one state for every check:

| State | Meaning |
| --- | --- |
| `PASS` | Real information exists, has been checked, and is approved. |
| `FAIL` | Information exists but violates a requirement or could not be verified. |
| `BLOCKED` | Required information, equipment, approval, or person is not yet available. |

Overall authorization is `GO` only when every required check is `PASS`. Any `FAIL` or `BLOCKED` result makes the overall result `NO-GO`.

## 3. Private test identity

Complete this section only in the private working copy.

| Field | Private value | Verified by | Status |
| --- | --- | --- | --- |
| Readiness-test date and time |  |  |  |
| Campaign ID |  |  |  |
| Site ID |  |  |  |
| Test lead |  |  |  |
| Field-test operator |  |  |  |
| Independent reviewer |  |  |  |
| Site/safety contact and adult/lab supervisor |  |  |  |
| Backup/recovery witness |  |  |  |
| Approved test location |  |  |  |
| Proposed 24-hour window |  |  |  |
| Gateway/computer asset ID |  |  |  |
| Approved client asset ID(s) |  |  |  |
| Networking equipment asset ID(s) |  |  |  |
| Reviewed `main` commit |  |  |  |
| Application/version reference |  |  |  |
| Local time zone |  |  |  |
| Dedicated field-database path |  |  |  |
| Evidence-directory path |  |  |  |
| Backup location |  |  |  |
| Recovery-copy location |  |  |  |

## 4. Required readiness checks

### P2E-PF-01 — Operator assigned

Pass criteria:

- One real field-test operator is named in the private record.
- The operator understands the approved procedure, stop conditions, and evidence rules.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-02 — Independent reviewer assigned

Pass criteria:

- One real reviewer is named in the private record.
- The reviewer is not the field-test operator.
- The reviewer agrees to inspect evidence and deviations independently.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-03 — Site/safety contact and adult/lab supervision approved

Pass criteria:

- A site/safety contact and an adult or qualified lab supervisor are named. One person may hold both roles only when formally authorized to do so.
- The supervisor has approved the location, equipment boundary, and proposed test window.
- The supervisor will be available for the parts of the test requiring physical or network action.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-04 — Test location approved

Pass criteria:

- The location is real, available, and approved by the responsible adult, lab, or property authority.
- The test will not interrupt production, school, employer, shared, or safety-critical systems.
- Private address details remain in the private record only.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-05 — Twenty-four-hour window approved

Pass criteria:

- Start and end date/time are recorded with a time zone.
- The window is at least 24 continuous hours.
- The operator, reviewer, and supervisor have confirmed availability for their assigned checkpoints.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-06 — Gateway and network equipment identified

Pass criteria:

- The real gateway/computer, approved clients, router/access point, backup targets, and non-sensing health-history device are inventoried with approved asset identifiers.
- Ownership or permission to use the equipment is confirmed.
- The equipment is isolated from production and safety-critical systems.
- Credentials and IP addresses are not copied into any public record.
- The reviewed `main` commit, application version, system time, and time zone are recorded.
- The complete automated suite passes on the field computer.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-07 — Dedicated field database prepared

Pass criteria:

- A dedicated database exists for the genuine field run.
- It is not the simulation database and does not contain relabeled simulation records.
- The operator has confirmed the application can open it without changing production data.
- The private path is recorded only in the private working copy.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-08 — Evidence directory prepared

Pass criteria:

- A dedicated evidence directory exists for this specific run.
- The directory is new or verified empty before the test.
- It contains the required `00_campaign` through `10_acceptance` directory structure from the controlled preflight record.
- `campaign_manifest.md`, `evidence_index.csv`, `deviation_log.csv`, `preflight_record.md`, and `repository_baseline.txt` are prepared in their required locations.
- File naming, timestamps, operator identity, evidence indexing, and checksum requirements are understood.
- The private path is not included in a public commit.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-09 — Backup and recovery separation verified

Pass criteria:

- A backup target exists and is writable.
- A separate recovery-copy location exists.
- Neither location reuses the simulation-results directory.
- A harmless test file can be copied and recovered without exposing credentials or private paths.
- The recovery verification will use a copy and cannot overwrite the active field database.
- A backup/recovery witness is assigned.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-10 — Rollback and stop conditions confirmed

Pass criteria:

- The operator and supervisor know how to end the test without touching unrelated systems.
- The approved procedure's stop conditions are reviewed.
- Any unexpected effect on an unrelated, shared, production, or safety-critical system causes an immediate stop and supervisor review.
- The gateway remains powered, the approved LAN remains available, and only the approved WAN test path may be interrupted.
- Physical sensors, sensor-payload ingestion, actuators, automated field actions, and electrical modifications remain prohibited.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-11 — Simulation separation confirmed

Pass criteria:

- The simulation loader will not run during the field test.
- `phase2e_simulation_schema.txt` and generated `results/` data will not be copied into the genuine field-evidence package.
- No simulation timestamp, record, screenshot, checksum, or result will be presented as field evidence.
- The field database filename excludes `simulation`, and the deployment mode is `field` with debug mode disabled.
- A unique non-development secret is confirmed without recording or exposing its value.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-12 — Privacy review completed

Pass criteria:

- The private record is stored outside public version control.
- Public files contain no signatures, private addresses, credentials, IP addresses, device secrets, or sensitive network paths.
- Any later Git-tracked version will replace sensitive values with neutral labels such as `VERIFIED-PRIVATE`.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-13 — Procedure and checkpoint review completed

Pass criteria:

- The operator, reviewer, and supervisor have reviewed `docs/12_PHASE2E_VERIFIED_FIELD_VALIDATION.md`.
- The checkpoint schedule, evidence requirements, deviation process, and acceptance boundary are understood.
- Responsibilities are assigned for the start, interim checkpoints, test end, backup, recovery, and review.
- The pre-outage, during-outage, device-health, export-inspection, and restart-test activities use genuine approved records and responsible people.
- The SQLite retention decision is recorded, and no database migration will occur during this campaign.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-14 — Private approvals recorded

Pass criteria:

- Operator approval is recorded in the private copy.
- Independent reviewer approval is recorded in the private copy.
- Test-lead, site/safety-contact, and adult/lab-supervisor approvals are recorded in the private copy.
- The independent reviewer is separate from the field operator.
- No signature image or personal contact information is placed in the public repository.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

### P2E-PF-15 — Final go/no-go review completed

Pass criteria:

- Checks P2E-PF-01 through P2E-PF-14 are all `PASS`.
- No unresolved deviation or safety concern remains.
- The reviewer and supervisor agree that the test may be scheduled within the approved boundary.
- The independent reviewer records `AUTHORIZED TO START PHASE 2E FIELD TEST` in the private controlled record.

Result: `PASS / FAIL / BLOCKED`

Evidence note:

## 5. Immediate no-go conditions

The final result must be `NO-GO` if any of these conditions is true:

- The independent reviewer is missing or is the same person as the operator.
- The adult/lab supervisor is missing or has not approved the activity.
- The test lead, site/safety contact, or backup/recovery witness is missing.
- The location or 24-hour window is not approved.
- The gateway, network equipment, or authority to use them is uncertain.
- The field database is missing, contains simulation data, or points to production data.
- The evidence, backup, or recovery location is missing or not separated as required.
- The work would interrupt an unrelated, shared, production, school, employer, or safety-critical system.
- A signature, private address, credential, IP address, device secret, or sensitive network path would be committed publicly.
- Any required check is `FAIL` or `BLOCKED`.

## 6. Test result summary

| Metric | Value |
| --- | --- |
| Required checks | 15 |
| Checks passed |  |
| Checks failed |  |
| Checks blocked |  |
| Open deviations |  |
| Overall result | `GO / NO-GO` |

Decision rule:

```text
GO = 15 PASS + 0 FAIL + 0 BLOCKED + 0 unresolved deviations
Otherwise = NO-GO
```

## 7. Private authorization

Complete this section only in the private copy.

| Role | Printed name | Decision | Date/time | Private signature or approval reference |
| --- | --- | --- | --- | --- |
| Field-test operator |  | `GO / NO-GO` |  |  |
| Independent reviewer |  | `GO / NO-GO` |  |  |
| Site/safety contact and adult/lab supervisor |  | `GO / NO-GO` |  |  |

Final authorization requires three `GO` decisions and a passing test summary. A passing readiness test authorizes only the scheduled Phase 2E field-validation run within the approved boundary. It does not authorize physical Phase 3 sensor integration.

## 8. Sanitized public status block

If a public status update is needed, publish only a sanitized block like this:

```text
Phase 2E preflight readiness test: PASS / FAIL / BLOCKED
Operator assignment: VERIFIED-PRIVATE / PENDING
Independent review: VERIFIED-PRIVATE / PENDING
Adult/lab supervision: VERIFIED-PRIVATE / PENDING
Approved location and window: VERIFIED-PRIVATE / PENDING
Dedicated field database: VERIFIED-PRIVATE / PENDING
Evidence, backup, and recovery preparation: VERIFIED-PRIVATE / PENDING
Field-test authorization: GO / NO-GO
Physical Phase 3: BLOCKED
```

Do not publish the private values used to reach the status.
