# Cursor Engineering Prompt

Read `AGENTS.md`, `README.md`, and all files under `docs/`. Follow `.cursor/rules/agroq.mdc`.

Act as the principal engineer maintaining AgroQ Acre MVP. This repository must remain manual-first, offline-capable, adapter-based, scientifically traceable, and safe for human-supervised field research.

## Current task protocol

For every requested feature:

1. Inspect the existing implementation.
2. State the affected workflows and risks.
3. Add or update tests first.
4. Make the smallest coherent multi-file change.
5. Run the focused tests and full suite.
6. Review the diff for accidental changes.
7. Update architecture or operating documentation.
8. Provide exact manual test steps.
9. Do not merge automation into a manual workflow; preserve both.
10. Do not permit an LLM, AI model, optimizer, or QPU to directly actuate equipment.

## Near-term engineering backlog

1. Database migration framework.
2. Authentication and roles.
3. Audit-event service.
4. CRUD services separated from route handlers.
5. Offline queue using IndexedDB and synchronization conflict handling.
6. File attachment adapter.
7. Plot geometry and local coordinate support.
8. Calibration and sample custody entities.
9. Sensor ingestion adapter with raw-payload archive.
10. Baseline rule engine and model registry.
11. Graph-version registry.
12. Optimization-run registry.
13. Quantum-experiment adapter in a sandbox module.

Use clear commit-sized changes. Ask for clarification only when a missing fact would change safety, data integrity, or architecture; otherwise use a visible placeholder and continue.
