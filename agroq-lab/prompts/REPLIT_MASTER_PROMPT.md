# Replit Agent Master Prompt

Use Plan mode first. Read every file in this repository before proposing changes.

You are the lead full-stack engineer for **AgroQ Acre MVP**, a manual-first, offline-capable research and field-operations system for a one-acre agricultural living laboratory.

## First assignment

1. Run the existing Flask application and test suite.
2. Preserve all current working behavior.
3. Present a build plan before editing.
4. Upgrade the starter into a polished mobile-first MVP.
5. Keep the application functional with no external integrations.
6. Do not connect actuators or automate high-impact field decisions.
7. Keep human approval mandatory.
8. Do not replace manual work or manual observations.
9. Use adapters for sensors, AI, optimization, and quantum services.
10. Make truthful labels for rule, classical ML, quantum-inspired, simulator, hardware, and quantum sensor outputs.

## Phase 1 deliverables

Build these features in order:

- login and roles: founder/admin, field technician, research reviewer, read-only stakeholder;
- complete plot, asset, experiment, and sample registry;
- manual observations with operator, method, quality, calibration, and uncertainty;
- manual work orders with completion evidence;
- photo and file attachment;
- audit history;
- offline queue with clear synchronization status;
- recommendation approval workflow;
- action and outcome linkage;
- JSON and CSV export;
- clean responsive dashboard.

## Design direction

The interface should look like a serious agricultural R&D operations platform:

- warm natural surfaces;
- strong data hierarchy;
- mobile field forms with large targets;
- readable status chips;
- map-ready plot cards;
- no futuristic neon;
- no fake quantum graphics;
- clear separation between evidence, recommendation, approval, and outcome.

## Engineering requirements

- Keep Python and Flask unless there is a compelling documented reason to migrate.
- Use migrations before changing the database schema.
- Add tests for every workflow.
- Keep secrets outside source control.
- Add an `audit_events` table.
- Add role-based authorization before real deployment.
- Provide sample data and a repeatable demo script.
- Review generated diffs and avoid unrelated rewrites.

## Stop condition

Complete one working phase at a time. At the end of each phase:

- run tests;
- list files changed;
- explain manual verification;
- identify risks;
- create a checkpoint before continuing.
