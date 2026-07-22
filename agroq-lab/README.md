# AgroQ Acre MVP Starter

This repository is the execution starter for the **AgroQ Quantum-AI Living Systems Lab**.

It is intentionally **manual-first and infrastructure-ready**:

- It works before sensors, radios, cloud services, AI models, or quantum services are connected.
- Field workers can enter observations, work logs, experiments, assets, and approvals manually.
- Offline browser entries are queued and synchronized when the gateway becomes reachable.
- Sensor, AI, optimization, and quantum modules are represented by explicit adapters and registries rather than being mixed into the core workflow.
- Human approval remains required for high-impact actions.

## MVP result

The first MVP should be a mobile-friendly field and research application with these working loops:

1. **Map and registry** — plots, assets, sensors, people, and experiments have IDs.
2. **Manual field loop** — a worker records an observation or task from a phone.
3. **Offline loop** — the entry is stored locally if disconnected and synchronized later.
4. **Evidence loop** — the dashboard shows raw observations, work performed, experiment context, and data quality.
5. **Recommendation loop** — a rule, AI model, or optimizer proposes an action.
6. **Human approval loop** — an authorized person approves, rejects, or edits the proposal.
7. **Outcome loop** — the result is measured and linked to the original decision.
8. **Export loop** — data can be exported for research, backup, or model development.

The included app is a functional scaffold for these loops. It is not a production control system and must not directly actuate irrigation, release organisms, or apply treatments without validated controls and safety review.

## Recommended toolchain

### Primary builder: Replit Agent

Use Replit Agent to import this repository, inspect the documents, run the app, improve the interface, and publish a shareable web MVP.

Start with `prompts/REPLIT_MASTER_PROMPT.md`.

### Engineering control: Cursor

Use Cursor after the first build for multi-file engineering, local gateway deployment, device adapters, test coverage, code review, and long-term repository maintenance.

Cursor project rules are included in `.cursor/rules/agroq.mdc`. Start with `prompts/CURSOR_MASTER_PROMPT.md`.

## Local run

```bash
python -m venv .venv
```

Windows:

```bat
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. You will be redirected to the local sign-in page.

## Local login (Phase 1A)

AgroQ now uses local username/password authentication with role-based access. Credentials are stored in the local SQLite database on this device. No external identity provider is used.

### Environment variables

| Variable | Purpose |
| --- | --- |
| `AGROQ_SECRET_KEY` | Flask session signing key. Required for production. |
| `AGROQ_ADMIN_USERNAME` | Initial administrator username, seeded only when the users table is empty. |
| `AGROQ_ADMIN_PASSWORD` | Initial administrator password, hashed before storage. Never logged or printed. |

### Development defaults (local setup only)

When the variables above are not set, the app uses development-only defaults:

- `AGROQ_SECRET_KEY`: `agroq-dev-secret-key-change-before-deployment`
- `AGROQ_ADMIN_USERNAME`: `admin`
- `AGROQ_ADMIN_PASSWORD`: `agroq-dev-change-me`

These defaults exist for local first-run convenience only. **Change all of them before any shared, staged, or production deployment.**

### Sign-in procedure

1. Start the app (`python app.py`).
2. Open `http://127.0.0.1:5000`.
3. Enter your local username and password on the sign-in page.
4. Use **Sign out** in the header to end the session.

The default site `AGQ-SITE-001` (AgroQ One-Acre Living Laboratory) and a single administrator account are seeded automatically on first database initialization.

### Role permissions

| Role | Access |
| --- | --- |
| `administrator` | Full application access: dashboard, observations, manual work, registry, approvals, and exports. |
| `researcher` | Observations, registry, experiments (via registry), exports, and recommendation approvals. |
| `field_operator` | Dashboard, observations, manual work, and registry viewing. |
| `viewer` | Dashboard and registry viewing only. |

Authorization is enforced on every protected route. Hidden navigation links do not grant access. No role may auto-execute a recommendation; human approval decisions remain limited to `approved`, `rejected`, or `edited`.

Successful sign-in and sign-out events are recorded in the local `audit_events` table for traceability.

## Phase 1E manual work orders and interventions

Manual work orders now link plots, assets, experiments, responsible users, due dates,
completion evidence, reviewer decisions, and append-only status history. Tasks marked as
requiring approval cannot be completed until an administrator or researcher records an
approval. The application records audit events for creation, evidence, review, and status
changes; it never executes a field intervention automatically.

## Phase 1F sample tracking and evidence attachments

Samples now retain experiment, treatment assignment, plot, collector, collection method,
collection time, storage location, and lifecycle status. Status changes are append-only and
require a reason. Photo and file evidence is registered through portable attachment metadata,
including its storage reference and optional SHA-256 checksum; binary files are not embedded
in SQLite. All sample and attachment changes are attributed and included in exports.

## Phase 1G offline synchronization and conflict handling

Offline observations now carry stable browser-generated request IDs and synchronize through
a bounded batch endpoint. The gateway stores a canonical SHA-256 payload fingerprint so exact
retries are idempotent and never duplicate an observation. Reused IDs with different content,
invalid linked records, and duplicate observation IDs are retained as conflicts instead of
overwriting evidence. Administrators and researchers explicitly dismiss a conflict or accept
its payload as a new immutable observation, with required decision notes and audit history.

## Phase 1D experiments and treatments

Experiments now have hypothesis and lifecycle records, reusable treatment definitions,
plot-level treatment assignments, responsible-user attribution, and outcome links to
immutable observations. Status changes require a reason and are retained in history.
Researchers and administrators may design experiments; field operators and viewers have
read-only access. Export endpoints include all Phase 1D records.
## Plot and asset registry (Phase 1B)

The registry now supports the complete local lifecycle for plots and assets:

- List and detail views for every authenticated role.
- Plot and asset creation and editing for administrators and researchers.
- Administrator-only retirement with POST confirmation; records are never permanently deleted.
- Validation for required values, allowed statuses, duplicate IDs, and asset-to-plot assignments.
- Plot detail views with assigned assets, experiments, and recent observations.
- Asset detail views with its assigned plot, revision, and recent observations.
- Automatic asset revision increments after material edits and retirement.
- Audit events for every create, update, and retire operation, attributed to the signed-in user.

### Registry permissions

| Role | Plot and asset permissions |
| --- | --- |
| `administrator` | View, create, edit, and retire. |
| `researcher` | View, create, and edit; cannot retire. |
| `field_operator` | View only. |
| `viewer` | View only. |

Retiring a plot is blocked while active assets, active experiments, or open manual tasks depend on it. Retired records and their scientific history remain available. Asset assignment is optional, but any supplied plot ID must exist.

Current limitations: IDs are generated locally from timestamps, there is no multi-user conflict resolution, and plot geometry/map editing is deferred to a later phase. The registry remains offline and SQLite-based with no external services.

## Manual observations and corrections (Phase 1C)

- Administrators, researchers, and field operators can record validated field observations.
- All authenticated roles can review the observation register and individual records.
- Raw observation rows are immutable through the application: no update or delete route exists.
- Mistakes are handled with linked correction records containing a reason, corrected value, quality flag, author, and timestamp.
- Observation creation and correction events are recorded in the audit trail.
- Plot, asset, source-type, quality-flag, unit, and numeric-value validation occurs before storage.
- JSON and CSV exports include correction history so evidence remains portable.

The original observation remains authoritative raw evidence. A correction adds interpretation without erasing what was first recorded.

## Run tests

```bash
pytest -q
```

## Core files

- `docs/00_MASTER_BUILD_BRIEF.md`
- `docs/01_MVP_SCOPE.md`
- `docs/02_MANUAL_OPERATIONS_PLAYBOOK.md`
- `docs/03_SYSTEM_ARCHITECTURE.md`
- `docs/04_DATA_MODEL.md`
- `docs/05_SCREEN_SPECIFICATION.md`
- `docs/06_HUMAN_APPROVAL_MATRIX.md`
- `docs/07_BUILD_PHASES.md`
- `docs/08_ACCEPTANCE_TESTS.md`
- `docs/09_INTEGRATION_ADAPTERS.md`
- `docs/10_MODEL_AND_QUANTUM_REGISTRY.md`
- `prompts/REPLIT_MASTER_PROMPT.md`
- `prompts/CURSOR_MASTER_PROMPT.md`

## Git discipline

Use one small branch per feature:

```text
feature/manual-observations
feature/offline-sync
feature/plot-map
feature/device-adapter
feature/model-registry
```

For each branch:

1. Update or add an acceptance test.
2. Make the smallest working change.
3. Run the test suite.
4. Review the diff.
5. Commit with a descriptive message.
6. Merge only after the manual workflow still works.
