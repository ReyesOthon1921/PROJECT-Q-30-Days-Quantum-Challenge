# Add AgroQ Q17-Q19 controlled-beta staging and validation

## Summary

This release candidate adds:

- Q17 staging acceptance and persistence verification
- Q18 beta-contact, interview, pilot-discovery, access-review, and invitation-policy operations
- Q19 demo evidence, claims-register, YC-update, and evidence-export operations
- separate Render staging frontend and backend Blueprint
- controlled-beta dashboard and protected APIs
- complete tests, CI workflow, runbooks, and local preflight

## Safety and release boundary

- No remote deployment is triggered.
- No production promotion is authorized.
- No physical field integration is authorized.
- No automatic equipment control is authorized.
- No quantum-advantage or unsupported agricultural performance claim is authorized.
- Staging acceptance requires verified persistence, evidence, backup, scientific gates, and a named administrator decision.
- Do not merge before real staging acceptance is completed and documented.

## Verification required before merge

- complete pytest suite
- dedicated Q17-Q19 suite
- Vite production build
- Q16 release preflight
- Q17-Q19 controlled-beta preflight
- Git diff checks
- real staging restart and redeployment persistence
- human demo evidence
- rollback checkpoint
