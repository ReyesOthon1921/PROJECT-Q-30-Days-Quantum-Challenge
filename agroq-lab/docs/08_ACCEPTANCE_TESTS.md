# MVP Acceptance Tests

| ID | Test | Pass condition |
|---|---|---|
| MVP-001 | Manual observation | A worker records and retrieves a measurement |
| MVP-002 | Offline queue | An observation entered offline remains on the device and synchronizes later |
| MVP-003 | Manual task | A task is created, assigned, completed, and retained |
| MVP-004 | Registry | Every displayed plot and asset has a unique ID |
| MVP-005 | Recommendation provenance | Recommendation shows source type and version |
| MVP-006 | Human gate | Pending recommendation cannot become an executed action automatically |
| MVP-007 | Export | JSON and CSV exports open and contain current records |
| MVP-008 | No-integration mode | All core demo steps work without external APIs |
| MVP-009 | Invalid decision | Unsupported approval state is rejected |
| MVP-010 | Reproducibility | A second computer can run the repository from README instructions |

## Later field acceptance

- 24-hour network outage.
- Power-cycle recovery.
- Duplicate and replay packet detection.
- Calibration traceability.
- Image upload under weak connectivity.
- Independent rebuild from controlled documentation.

## Phase 2E release gate

- Run the complete automated suite and retain its result.
- Generate `results/phase2e/phase2e_acceptance.json` and `.md` with
  `python scripts/phase2e_acceptance.py`.
- Complete the operator checks in `docs/11_PHASE2_FIELD_ACCEPTANCE.md`.
- Do not begin Phase 3 unless every automated gate passes and the manual review is signed.
