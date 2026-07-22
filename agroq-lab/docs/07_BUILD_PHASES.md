# Build Phases

## Phase 0 — Controlled starter

- Commit this repository.
- Run tests.
- Confirm manual forms and exports.
- Add project owner and site placeholders.

## Phase 1 — Manual-first MVP

- Authentication and roles.
- Complete plot and asset CRUD.
- Experiment design and sample tracking.
- Photo/file attachments.
- Audit history.
- Better offline queue and conflict handling.

Exit test: a team can run one week of field work without sensors.

## Phase 2 — Local gateway

- Deploy to a field computer.
- Local network name and secure access.
- Automatic backups.
- Database migration to PostgreSQL if needed.
- Device registry and health page.

Exit test: application operates through a 24-hour internet outage.

## Phase 3 — First sensor adapter

- Ingest one prototype node.
- Preserve raw payload.
- Normalize to observation schema.
- Compare with manual measurements.
- Device diagnostics and firmware version.

Exit test: sensor failure does not block manual work.

## Phase 4 — Baseline intelligence

- Threshold rules.
- Missing-data and drift checks.
- Simple forecasting.
- Recommendation records.
- Human decision and outcome linkage.

Exit test: every recommendation is traceable and comparable with a baseline.

## Phase 5 — Graph and experiment intelligence

- Spatial graph.
- Laplacian anomaly score.
- Active sampling.
- Bayesian experiment selection.
- Biological interaction graph.

## Phase 6 — Quantum research lane

- Freeze benchmark datasets.
- Define QUBO and classical solvers.
- Add simulator adapter.
- Record QPU backend, shots, noise, queue time, seed, and result.
- Publish no advantage claim without matched evidence.
