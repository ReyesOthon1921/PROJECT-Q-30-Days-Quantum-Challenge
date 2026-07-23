# Phase 2E Verified-Field Validation Preparation

Document status: **Controlled field-test procedure**
Applies to: AgroQ local field gateway, Phase 2E
Prepared: 2026-07-22
Entry state: Phase 2E simulation rehearsal passed; verified field acceptance pending
Safety gate: **Physical Phase 3 sensor integration remains blocked until this procedure is completed and approved.**

## 1. Purpose and boundary

This procedure prepares and records genuine field evidence for the seven Phase 2E gates:

- `P2E-OUTAGE` — 24-hour outage operation;
- `P2E-BACKUP` — backup creation and recovery verification;
- `P2E-DEVICE` — real device registration and append-only health history;
- `P2E-MANUAL` — manual field workflow retention;
- `P2E-AUDIT` — audit-history retention;
- `P2E-LAN` — safe local-network readiness;
- `P2E-MIGRATION` — documented database decision.

This is not Phase 3. Do not connect a physical sensor, ingest a sensor payload, control irrigation, operate an actuator, or apply a treatment during this validation. The permitted device for `P2E-DEVICE` is the actual field gateway, workstation, phone/tablet client, or a non-sensing prototype node used in the test.

The outage exercise is a controlled **internet/WAN outage**. Keep the gateway and approved local network powered. Do not disconnect building wiring, open electrical equipment, defeat protective devices, or interrupt safety-critical services. Any electrical work outside ordinary plug-and-switch operation belongs to a qualified adult or technician under the site safety plan.

## 2. Definition of verified field evidence

Evidence qualifies as `field` only when all of the following are true:

1. It was produced on the identified field hardware and field LAN during the dated campaign.
2. The actual operator, reviewer, site, gateway, database path, start time, and end time are recorded.
3. Records were created through the application or its documented controls—not inserted or edited directly in SQLite.
4. Original failures, warnings, and deviations are retained. A rerun receives a new campaign or attempt ID.
5. Raw evidence files remain unchanged after capture; corrections are documented separately.
6. Evidence contains no passwords, session secrets, private keys, or unnecessary personal information.
7. Simulation records and the simulation loader are absent from the field database.

The following do **not** qualify: screenshots of the simulation database, copied simulation rows, shortened or backdated outage records, manually edited acceptance JSON, fabricated device events, or a report relabeled from `simulation` to `field`.

## 3. Roles and separation of duties

| Role | Responsibility |
|---|---|
| Test lead | Creates the campaign, controls scope, confirms preconditions, and records deviations. |
| Field operator | Performs the manual workflow and checkpoints on the field hardware. |
| Independent reviewer | Opens evidence, repeats the startup/export check, and approves or blocks each gate. |
| Site/safety contact | Confirms the outage plan will not affect safety-critical, shared, or production systems. |

The independent reviewer must not merely accept the operator's description. They must inspect the referenced files and application records. One person may perform more than one operational role when staffing is limited, but final Phase 3 authorization still requires a separate reviewer.

## 4. Campaign identity and evidence storage

Assign one immutable campaign ID:

```text
AGQ-P2E-FIELD-YYYYMMDD-01
```

Use a dedicated field database and evidence folder. Never reuse the simulation database.

```text
instance\agroq_phase2_field_validation.db
results\phase2e_field\AGQ-P2E-FIELD-YYYYMMDD-01\
```

Recommended evidence structure:

```text
00_campaign
01_preflight
02_lan
03_manual_workflow
04_device_health
05_backup_recovery
06_audit_history
07_outage_24h
08_exports_and_restart
09_migration
10_acceptance
```

The `results\` evidence remains outside source-control commits. Copy the completed evidence bundle to the approved protected backup location after review.

## 5. Campaign cover sheet

Complete this before testing.

| Field | Entry |
|---|---|
| Campaign ID |  |
| Site ID and location |  |
| Gateway name and asset ID |  |
| Field database path |  |
| Evidence directory |  |
| Git commit on `main` |  |
| Test lead |  |
| Field operator |  |
| Independent reviewer |  |
| Site/safety contact |  |
| Planned start (local time and UTC) |  |
| Planned finish (local time and UTC) |  |
| Approved outage boundary | Internet/WAN only; local gateway and LAN remain powered |
| Physical sensors connected? | Must be **No** |
| Actuators or automated field actions enabled? | Must be **No** |

## 6. Preflight checklist

Mark each item `PASS`, `BLOCKED`, or `N/A` with a reason. Any blocked required item stops the campaign.

| ID | Preflight item | Required evidence | Result |
|---|---|---|---|
| PF-01 | Repository is on reviewed `main`; commit ID recorded | `git log -1 --oneline` capture |  |
| PF-02 | Working tree contains no unexplained tracked changes | `git status --short` capture |  |
| PF-03 | Complete automated suite passes on field computer | Saved `python -m pytest -q` output |  |
| PF-04 | Dedicated field DB path is used; filename does not contain `simulation` | Campaign cover sheet and startup capture |  |
| PF-05 | Simulation loader will not be run against the field DB | Test-lead initials |  |
| PF-06 | System clock, time zone, and date are correct | Clock/time-zone capture |  |
| PF-07 | Gateway, local router/access point, client, and backup location are identified | Asset list or photograph with IDs |  |
| PF-08 | No sensor, actuator, irrigation controller, or treatment system is connected | Operator and reviewer inspection |  |
| PF-09 | Internet/WAN outage is approved and isolated from shared or safety-critical services | Site/safety approval |  |
| PF-10 | LAN secret is unique and not the development default; debug is false | Status page/config summary with secret redacted |  |
| PF-11 | Field operator and independent reviewer can sign in with their own accounts | Role/access check |  |
| PF-12 | Blank deviation log and evidence index are ready | Files in `00_campaign` |  |

Suggested Windows CMD session values:

```bat
set "CAMPAIGN_ID=AGQ-P2E-FIELD-YYYYMMDD-01"
set "AGROQ_DB_PATH=instance\agroq_phase2_field_validation.db"
set "AGROQ_GATEWAY_NAME=agroq-acre-gateway"
set "AGROQ_SITE_ID=AGQ-SITE-001"
set "AGROQ_DEPLOYMENT_MODE=field"
set "AGROQ_BIND_HOST=0.0.0.0"
set "AGROQ_PORT=5000"
set "AGROQ_DEBUG=false"
```

Set `AGROQ_SECRET_KEY` locally to a long, unique value, but never display or save the value in evidence. Confirm only that `secret_configured` is true.

## 7. Evidence-collection rules

For every evidence item, record:

```text
Evidence ID
Campaign ID
Gate ID
Original filename
Description
Source system or screen
Operator
Captured-at time with UTC offset
Related database record IDs
SHA-256 checksum
Reviewer result: accepted / rejected
Reviewer notes and date
```

Use filenames that preserve order and meaning:

```text
P2E-<GATE>_<sequence>_<YYYYMMDDTHHMMSS-offset>_<description>.<ext>
```

Examples:

```text
P2E-LAN_001_20260725T090000-0700_gateway-status.png
P2E-BACKUP_003_20260725T103500-0700_recovery-verification.txt
P2E-OUTAGE_006_20260726T091000-0700_final-checkpoint.png
```

Create a SHA-256 value after each file is captured:

```bat
certutil -hashfile "path\to\evidence-file" SHA256
```

Copy the resulting hash into the evidence index. Do not edit the original file after hashing. If redaction is necessary, keep the protected original and create a separately named redacted copy with its own checksum.

## 8. Gate procedures and pass criteria

### 8.1 `P2E-LAN` — safe LAN readiness

Procedure:

1. Start the gateway using the reviewed launcher and field environment.
2. Open the authenticated gateway-status page on the field computer.
3. Connect one approved client to the same isolated or approved LAN and open the application by the gateway's local address.
4. Confirm deployment mode is `field`, debug is `false`, the database is available, and internet is not required.
5. Confirm the application is not exposed through router port forwarding or a public tunnel.
6. Save a status-page capture and a redacted configuration summary. Do not capture secrets.

Pass criteria:

- `gateway_configuration().deployment_ready` is true;
- debug is false;
- a non-development secret is configured;
- the approved client reaches the gateway over LAN;
- no unintended public exposure is present.

Required evidence: gateway-status capture, client-access capture, configuration summary, operator/reviewer initials.

### 8.2 `P2E-MANUAL` — manual field workflow

Procedure:

1. Before the WAN outage, create one clearly labeled field-validation plot or use an approved real plot.
2. Record one genuine manual observation with time, method/instrument, value, unit, operator, quality flag, and field conditions.
3. Create a manual inspection task linked to the appropriate plot or asset.
4. Move the task through the documented human workflow and attach or reference completion evidence.
5. Retrieve the observation and task from a second page or approved client.
6. During the WAN outage, record a second genuine manual observation. If the browser is disconnected from the gateway, confirm it remains queued locally and synchronizes after gateway access returns.
7. Never overwrite the original observation. If a correction is needed, use the correction workflow.

Pass criteria:

- at least one genuine manual observation is retained in the field DB;
- the record has required scientific context and operator attribution;
- linked work/evidence is retrievable without an external API;
- any correction is append-only;
- offline queue behavior, when exercised, retains and later synchronizes the entry without duplication.

Required evidence: observation ID(s), task ID, screenshots, queue/synchronization result if used, and JSON/CSV export references.

### 8.3 `P2E-DEVICE` — device registry and health history

Procedure:

1. Register the actual gateway, workstation, approved client, or non-sensing prototype node used in the campaign. Do not register an imaginary sensor.
2. Record its device ID, device type, local network address or approved identifier, firmware/OS version if available, and initial status.
3. Record a manual inspection health event with diagnostic result and notes.
4. Record a heartbeat or reasoned status change later in the campaign.
5. Reopen the device detail page and confirm the earlier event remains in append-only history.

Pass criteria:

- at least one genuine, non-retired device exists;
- at least one attributed health event exists;
- history shows real timestamps and the actual device identity;
- no physical sensor integration or fabricated sensor data was used.

Required evidence: device ID, asset label/photo where appropriate, device page capture, health-event IDs, and export row.

### 8.4 `P2E-BACKUP` — backup and recovery

Procedure:

1. Confirm a known observation and audit event exist in the active field DB.
2. From the administrator gateway page, create a local backup.
3. Record the backup ID, filename, file size, creation time, trigger type, and application verification message.
4. Run the documented recovery verification. Verification must use a recovery copy and must not overwrite the active field DB.
5. Open the recovery copy read-only or through the approved verification function and confirm SQLite integrity plus the known observation and audit record.
6. Keep the original backup and verification result in the protected campaign evidence location.

Pass criteria:

- `backup_runs.status` is `verified`;
- the backup has a nonzero size and recorded `verified_at` time;
- integrity/recovery verification succeeds;
- the known manual observation and audit record are present in the recovery copy;
- the active field DB was not replaced during the test.

Required evidence: backup ID, file metadata, verification capture/message, recovery-copy check, SHA-256 checksum, reviewer initials.

### 8.5 `P2E-AUDIT` — audit-history retention

Procedure:

1. Identify audit events created by the manual observation, task, device, backup, and outage workflows.
2. Confirm each selected event contains an action, entity type, entity ID, attributed user, and timestamp.
3. Cross-check at least three audit events against their related application records.
4. Export the audit history through the approved export path if available, or retain a read-only query/report produced by the application procedure.
5. Confirm no earlier audit event was overwritten or deleted during the campaign.

Pass criteria:

- genuine audit events exist in the field DB;
- selected events match their related records and operators;
- history remains available during the WAN outage and after gateway restart;
- discrepancies are documented and block the gate until resolved and retested.

Required evidence: audit IDs, related entity IDs, cross-check table, capture/export, reviewer notes.

### 8.6 `P2E-OUTAGE` — measured 24-hour WAN outage

Procedure:

1. Confirm PF-09 approval and verify that no safety-critical or shared service depends on the test connection.
2. Start the outage test in the gateway application while the field gateway is online.
3. Record the application-generated outage-test ID and start time.
4. Disconnect only the approved internet/WAN path. Keep the gateway, local LAN, and approved clients powered and available.
5. At approximately start, 6, 12, 18, and 24 hours, record a checkpoint. At every checkpoint confirm:
   - the database opens;
   - the manual workflow operates;
   - a local backup or the latest verified backup remains available;
   - the gateway status page is reachable over LAN.
6. During the outage, create or retrieve genuine manual-workflow evidence and inspect device health.
7. After at least 24 continuous measured hours, complete the outage test in the application. Do not edit timestamps.
8. Restore the WAN connection, confirm normal local operation, and synchronize any legitimately queued client entry once.

Pass criteria:

- the application records at least 24 continuous elapsed hours;
- the outage test status is `passed`;
- checkpoints are genuine and include at least one application-recorded checkpoint; the campaign target is five;
- database, manual workflow, backup availability, and LAN access remain functional;
- there is no loss, overwrite, or duplicate synchronization of field records.

Required evidence: outage-test ID, start/end captures, checkpoint IDs and captures, observation/task IDs used during outage, reconnect/sync result, deviation log.

If the gateway or local LAN fails, preserve the evidence, mark the attempt failed, restore normal safe service, diagnose the cause, and schedule a new attempt. Never shorten or backdate the record to obtain a pass.

### 8.7 `P2E-MIGRATION` — database decision

Procedure:

1. Review the current Phase 2 decision: SQLite is retained for one offline local gateway and a small operator team.
2. Evaluate each migration trigger using campaign observations:
   - sustained concurrent-writer lock contention;
   - multiple gateways requiring one authoritative database;
   - documented volume or latency target missed;
   - centralized high availability or managed replication required;
   - access-control or audit requirements exceeding the local model.
3. Record `met`, `not met`, or `not measured` for each trigger with evidence.
4. Reopen the migration project only when at least two triggers are met. Migration is a separate tested checkpoint and is not performed during this campaign.

Pass criteria:

- the decision and trigger review are dated and signed;
- SQLite remains approved, or a separate migration checkpoint is opened;
- no unreviewed database migration occurred during field validation.

Required evidence: completed trigger table, decision statement, responsible reviewer approval.

## 9. Required manual release checks

These checks supplement the seven report gates and are mandatory even if the JSON report passes.

| ID | Manual release check | Pass evidence | Result |
|---|---|---|---|
| MR-01 | JSON export opens and contains current field records | Filename, checksum, reviewer initials |  |
| MR-02 | CSV exports for observations, devices, health events, backups, outage tests, and checkpoints open correctly | File list and reviewer initials |  |
| MR-03 | A second operator independently starts the gateway from the README/launcher | Startup capture and operator notes |  |
| MR-04 | Gateway restarts without loss of the known observation, audit event, device event, or backup record | Before/after record-ID comparison |  |
| MR-05 | No external API is required for the core manual workflow | Operator and reviewer confirmation |  |
| MR-06 | No physical sensor or actuator was connected | Final inspection |  |
| MR-07 | Evidence index is complete; every retained file has a SHA-256 value | Reviewed evidence index |  |
| MR-08 | Failures and deviations are closed or explicitly accepted by the responsible reviewer | Deviation log |  |
| MR-09 | Source tree is clean except approved untracked field evidence | `git status --short` capture |  |

## 10. Final acceptance run

Run the complete automated suite on the field computer and save its output:

```bat
python -m pytest -q
```

Then run acceptance against the dedicated field database:

```bat
python -m scripts.phase2e_acceptance --evidence-mode field --db "instance\agroq_phase2_field_validation.db" --output "results\phase2e_field\%CAMPAIGN_ID%\10_acceptance"
```

Display and preserve both generated reports:

```bat
type "results\phase2e_field\%CAMPAIGN_ID%\10_acceptance\phase2e_acceptance.md"
type "results\phase2e_field\%CAMPAIGN_ID%\10_acceptance\phase2e_acceptance.json"
```

Expected technical result only after genuine field evidence exists:

```json
"evidence_mode": "field",
"technical_acceptance_passed": true,
"release_status": "ready_for_phase3",
"phase3_sensor_integration_allowed": true
```

Do not edit the report. A `blocked` result is a valid safety outcome and must remain preserved with the evidence bundle.

## 11. Final gate checklist

| Gate | Pass condition | Primary evidence references | Operator | Reviewer | Result |
|---|---|---|---|---|---|
| P2E-OUTAGE | Genuine 24-hour WAN outage passed |  |  |  |  |
| P2E-BACKUP | Backup recovery verified without overwriting active DB |  |  |  |  |
| P2E-DEVICE | Actual non-retired device plus append-only health history |  |  |  |  |
| P2E-MANUAL | Genuine manual records retained offline/local |  |  |  |  |
| P2E-AUDIT | Attributed audit history cross-checked and retained |  |  |  |  |
| P2E-LAN | Safe field LAN configuration and approved client access |  |  |  |  |
| P2E-MIGRATION | SQLite/migration decision reviewed and signed |  |  |  |  |
| MANUAL-RELEASE | MR-01 through MR-09 all pass |  |  |  |  |

## 12. Deviation log

| Deviation ID | Time | Gate | What occurred | Impact | Containment | Retest required? | Owner | Status |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |

A deviation remains open until the responsible reviewer accepts the resolution and identifies the evidence. Open safety, integrity, traceability, recovery, or access-control deviations block Phase 3.

## 13. Authorization decision

Phase 3 may begin only when all of the following are true:

- every technical Phase 2E gate passes using `evidence_mode = field`;
- every manual release check passes;
- the full automated suite passes on the field computer;
- all required evidence is indexed, checksummed, and reviewed;
- no blocking deviation remains;
- the independent reviewer signs the release;
- the source tree is clean apart from approved untracked evidence;
- the first Phase 3 sensor adapter is separately scoped as read-only with raw-payload preservation, normalization, comparison to manual measurements, and failure isolation.

If any item is false, record:

```text
Verified field acceptance: BLOCKED
Physical Phase 3 sensor integration: NOT AUTHORIZED
```

Final decision:

| Approval | Name | Decision | Date/time | Signature or recorded approval reference |
|---|---|---|---|---|
| Test lead |  | PASS / BLOCKED |  |  |
| Field operator |  | PASS / BLOCKED |  |  |
| Independent reviewer |  | APPROVED / BLOCKED |  |  |
| Site/safety contact |  | APPROVED / BLOCKED |  |  |

Phase 3 authorization reference (leave blank unless every condition passes): ____________________
