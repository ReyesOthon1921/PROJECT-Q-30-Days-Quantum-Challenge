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

Open `http://127.0.0.1:5000`.

## Run tests

```bash
pytest -q
```

## Demo login

This scaffold has no authentication yet. Authentication and role-based access are Phase 2 requirements before real deployment.

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
