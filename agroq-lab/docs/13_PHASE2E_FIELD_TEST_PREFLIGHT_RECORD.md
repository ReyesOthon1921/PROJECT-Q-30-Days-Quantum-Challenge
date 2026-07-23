# Phase 2E Verified-Field Test Preflight Record

Document status: **Controlled preflight record**

Applies to: AgroQ local field gateway, Phase 2E

Prepared: 2026-07-22

Entry state: Field-validation procedure approved; verified field execution not started

Safety gate: **This record may authorize a controlled Phase 2E field test only. It cannot authorize Phase 3 sensor integration.**

## 1. Purpose

Complete this record before scheduling or starting the genuine Phase 2E verified-field campaign. Its purpose is to prove that the people, equipment, database, evidence locations, backup plan, network boundary, and test window are ready.

Do not collect acceptance evidence until every required preflight item is marked `PASS` and the independent reviewer records `AUTHORIZED TO START PHASE 2E FIELD TEST`.

This preflight does not permit physical-sensor connection, sensor-payload ingestion, actuator operation, irrigation control, treatment application, electrical modification, or any other Phase 3 activity.

## 2. Preflight status

Select one status:

- [ ] `DRAFT` — required information is still missing.
- [ ] `BLOCKED` — one or more required controls failed.
- [ ] `READY FOR REVIEW` — the test lead completed the record.
- [ ] `AUTHORIZED TO START PHASE 2E FIELD TEST` — the independent reviewer approved the controlled test.

Current status: ____________________

Status recorded by: ____________________

Date/time with UTC offset: ____________________

## 3. Campaign identity

| Field | Required entry |
|---|---|
| Campaign ID | `AGQ-P2E-FIELD-YYYYMMDD-01` |
| Site ID |  |
| Site description |  |
| Gateway asset ID |  |
| Gateway name |  |
| Approved client asset ID(s) |  |
| Git commit on reviewed `main` |  |
| Application/version reference |  |
| Dedicated field DB | `instance\agroq_phase2_field_validation.db` or an approved campaign-specific field path |
| Evidence root | `results\phase2e_field\<CAMPAIGN_ID>` |
| Protected evidence-copy location |  |
| Local time zone |  |

Campaign IDs and evidence paths must not be reused for reruns. A failed attempt receives a new attempt number or campaign ID.

## 4. Assigned people and separation of duties

| Role | Name | Contact or team reference | Responsibility accepted? | Date/time |
|---|---|---|---|---|
| Test lead |  |  | YES / NO |  |
| Field operator |  |  | YES / NO |  |
| Independent reviewer |  |  | YES / NO |  |
| Site/safety contact |  |  | YES / NO |  |
| Backup/recovery witness |  |  | YES / NO |  |

The person granting final preflight authorization must be separate from the field operator. The site/safety contact must confirm that the planned WAN outage affects no shared, production, emergency, or safety-critical service.

## 5. Planned test window

| Event | Local date/time with UTC offset | UTC date/time | Responsible person |
|---|---|---|---|
| Preflight review |  |  |  |
| Campaign start |  |  |  |
| WAN outage begins |  |  |  |
| T+6-hour checkpoint |  |  |  |
| T+12-hour checkpoint |  |  |  |
| T+18-hour checkpoint |  |  |  |
| T+24-hour checkpoint |  |  |  |
| WAN restored |  |  |  |
| Acceptance review |  |  |  |

The outage interval must provide at least 24 continuous measured hours. Do not shorten, backdate, or manually alter timestamps.

## 6. Approved test boundary

Complete every line:

| Boundary control | Required answer | Recorded answer | Reviewer initials |
|---|---|---|---|
| Internet/WAN path affected | Approved test path only |  |  |
| Local gateway remains powered | YES |  |  |
| Approved LAN remains available | YES |  |  |
| Shared or production network affected | NO |  |  |
| Safety-critical service affected | NO |  |  |
| Physical sensors connected | NO |  |  |
| Sensor payloads ingested | NO |  |  |
| Actuators or automated field actions enabled | NO |  |  |
| Electrical equipment opened or modified | NO |  |  |
| Simulation loader used | NO |  |  |
| Simulation DB or copied simulation rows used | NO |  |  |

Any answer that differs from the required answer blocks the test. Network interruption or equipment work must remain within an approved test environment and the site plan, with qualified adult/lab supervision where required.

## 7. Environment inventory

| Item | Asset ID or approved identifier | Version/configuration | Location | Ready? | Evidence reference |
|---|---|---|---|---|---|
| Field gateway computer |  |  |  |  |  |
| Local router/access point |  |  |  |  |  |
| Approved client 1 |  |  |  |  |  |
| Approved client 2, if used |  |  |  |  |  |
| Primary local backup target |  |  |  |  |  |
| Protected evidence-copy target |  |  |  |  |  |
| Non-sensing device for health history |  |  |  |  |  |

Do not record passwords, secret values, private keys, or unnecessary personal information.

## 8. Dedicated field database control

| Control | Entry |
|---|---|
| Approved database path |  |
| Filename excludes the word `simulation` | PASS / BLOCKED |
| Database is separate from all rehearsal databases | PASS / BLOCKED |
| Simulation loader prohibited and absent from the field workflow | PASS / BLOCKED |
| Database owner/custodian |  |
| Initial database size and created-at time |  |
| Initial SHA-256, if captured |  |
| Recovery-copy location |  |

Database records must be created through the application or documented controls. Direct database editing to satisfy an acceptance gate is prohibited.

## 9. Evidence package readiness

The evidence root must contain these directories before the campaign starts:

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

Required blank control files:

| File | Purpose | Present? | Reviewer initials |
|---|---|---|---|
| `00_campaign\campaign_manifest.md` | Campaign identity and scope |  |  |
| `00_campaign\evidence_index.csv` | Evidence IDs, paths, checksums, and reviews |  |  |
| `00_campaign\deviation_log.csv` | Failures, containment, owners, and closure |  |  |
| `01_preflight\preflight_record.md` | Completed copy of this record |  |  |
| `01_preflight\repository_baseline.txt` | Commit, status, and test-suite output references |  |  |

The `results\` evidence package remains untracked. It must not be added to a source-code commit.

## 10. Repository and software baseline

Record evidence from the field computer:

| ID | Check | Required result | Evidence reference | Result |
|---|---|---|---|---|
| PF-01 | `git log -1 --oneline` | Reviewed `main` commit recorded |  |  |
| PF-02 | `git status --short` | No unexplained tracked changes |  |  |
| PF-03 | `python -m pytest -q` | Complete suite passes |  |  |
| PF-04 | Field launcher/README reviewed | Independent operator can follow it |  |  |
| PF-05 | System date, time, and time zone checked | Correct and recorded |  |  |
| PF-06 | Debug mode | `false` |  |  |
| PF-07 | Deployment mode | `field` |  |  |
| PF-08 | Unique non-development secret configured | Confirmed without revealing value |  |  |
| PF-09 | Gateway database available | Dedicated field path confirmed |  |  |

Untracked simulation artifacts may remain outside the commit, but they must not be copied into the field evidence package or field database.

## 11. Backup and recovery preflight

| Check | Entry or evidence reference | Result |
|---|---|---|
| Primary backup destination exists and has sufficient space |  |  |
| Protected evidence-copy destination exists |  |  |
| Recovery verification uses a copy, never the active DB |  |  |
| Backup/recovery witness assigned |  |  |
| Known observation and audit IDs will be selected before recovery verification |  |  |
| Failure procedure preserves the original backup and active DB |  |  |

The recovery test must not overwrite the active field database.

## 12. Manual workflow and device plan

| Planned evidence | Approved record or action | Responsible person | Ready? |
|---|---|---|---|
| Field-validation plot or approved real plot |  |  |  |
| Genuine pre-outage manual observation |  |  |  |
| Manual inspection task |  |  |  |
| Genuine during-outage manual observation |  |  |  |
| Actual gateway/client/non-sensing device record |  |  |  |
| Initial manual health event |  |  |  |
| Later heartbeat or status event |  |  |  |
| Independent export inspection |  |  |  |
| Independent restart test |  |  |  |

Do not invent sensor identities or fabricate sensor measurements. The device-health gate may use the actual gateway, workstation, approved client, or a non-sensing prototype node.

## 13. Migration decision preflight

Record the current decision before testing:

```text
SQLite is retained for Phase 2 unless at least two documented migration triggers are met. No database migration will occur during this campaign.
```

| Migration trigger | Current state: met / not met / not measured | Evidence reference |
|---|---|---|
| Sustained concurrent-writer lock contention |  |  |
| Multiple gateways require one authoritative database |  |  |
| Documented volume or latency target is missed |  |  |
| Centralized high availability or managed replication is required |  |  |
| Access-control or audit needs exceed the local model |  |  |

## 14. Stop and rollback conditions

Stop the campaign safely and record a deviation if any of the following occurs:

- the local gateway or approved LAN becomes unavailable;
- a shared, production, emergency, or safety-critical service could be affected;
- the wrong database or evidence directory is active;
- a secret or unnecessary personal information appears in evidence;
- the active field database could be overwritten;
- timestamps, audit history, or raw evidence appear altered;
- a sensor, actuator, or automated field action is introduced;
- an operator cannot complete the manual workflow safely;
- the approved site/safety contact withdraws approval.

Safe response:

1. Preserve existing logs and evidence without editing them.
2. Restore the approved normal WAN/network state when safe and authorized.
3. Keep the active database and backups unchanged.
4. Record the event in `deviation_log.csv`.
5. Mark the attempt `BLOCKED` or `FAILED`.
6. Diagnose and review before assigning a new attempt or campaign ID.

## 15. Preflight checklist and decision

| ID | Required item | Result: PASS / BLOCKED | Evidence or notes | Reviewer initials |
|---|---|---|---|---|
| PF-01 | Reviewed `main` commit recorded |  |  |  |
| PF-02 | Working tree has no unexplained tracked changes |  |  |  |
| PF-03 | Complete automated suite passes |  |  |  |
| PF-04 | Dedicated field DB approved |  |  |  |
| PF-05 | Simulation loader and data excluded |  |  |  |
| PF-06 | Date, time, and time zone verified |  |  |  |
| PF-07 | Gateway, LAN, clients, and backup targets identified |  |  |  |
| PF-08 | Sensors, actuators, and automated actions absent |  |  |  |
| PF-09 | WAN outage boundary approved and isolated |  |  |  |
| PF-10 | Debug false and unique secret configured |  |  |  |
| PF-11 | Operator and reviewer accounts verified |  |  |  |
| PF-12 | Evidence index and deviation log ready |  |  |  |
| PF-13 | Backup/recovery witness and recovery-copy plan ready |  |  |  |
| PF-14 | Planned 24-hour checkpoints assigned |  |  |  |
| PF-15 | Stop/rollback procedure reviewed |  |  |  |

Required count: 15 `PASS`, 0 `BLOCKED`.

Open deviations at authorization time: ____________________

Preflight decision:

- [ ] `BLOCKED — DO NOT START`
- [ ] `AUTHORIZED TO START PHASE 2E FIELD TEST`

Decision notes: ____________________

| Approval | Name | Decision | Date/time with UTC offset | Signature or recorded approval reference |
|---|---|---|---|---|
| Test lead |  | READY / BLOCKED |  |  |
| Field operator |  | ACCEPTED / BLOCKED |  |  |
| Independent reviewer |  | AUTHORIZED / BLOCKED |  |  |
| Site/safety contact |  | APPROVED / BLOCKED |  |  |

## 16. Boundary after preflight

If authorized, the next action is the controlled Phase 2E verified-field campaign described in `docs/12_PHASE2E_VERIFIED_FIELD_VALIDATION.md`.

Authorization from this record means only:

```text
Phase 2E verified-field execution: MAY START WITHIN THE APPROVED WINDOW
Physical Phase 3 sensor integration: NOT AUTHORIZED
```

If any required item is blocked or unsigned, record:

```text
Phase 2E verified-field execution: BLOCKED
Physical Phase 3 sensor integration: NOT AUTHORIZED
```
