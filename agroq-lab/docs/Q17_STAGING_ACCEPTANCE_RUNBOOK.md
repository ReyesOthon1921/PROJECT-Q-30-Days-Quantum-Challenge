# AgroQ Q17 Staging Acceptance Runbook

## Boundary

Q17 verifies an explicitly deployed staging environment. It does not trigger deployment, promote production, authorize physical field integration, or approve advanced performance claims.

## Required acceptance checks

1. Backend health
2. Frontend overview
3. 3D Digital Acre
4. Access & Community
5. Quantum Lab
6. Administrator login
7. Public access request
8. Beta reservation
9. Invitation redemption
10. Administrator access review
11. Restart persistence
12. Replacement-deployment persistence
13. Manual release boundary
14. Rollback checkpoint

Every required check must be `passed` or formally marked `not_applicable` with evidence and notes.

## Prepare staging evidence

After an operator explicitly deploys the release candidate:

```cmd
python agroq-lab\staging_acceptance_cli.py ^
  --mode prepare ^
  --base-url https://STAGING-DOMAIN ^
  --username STAGING-ADMIN ^
  --password STAGING-PASSWORD ^
  --commit-sha RELEASE-COMMIT ^
  --release-tag RELEASE-TAG ^
  --service-id STAGING-SERVICE-ID ^
  --state agroq-lab\results\controlled_beta\staging_state.json
```

This command:

- checks public routes;
- authenticates;
- creates the staging-candidate record;
- records automatable acceptance checks;
- creates a persistence sentinel;
- records the pre-restart sentinel observation.

## Restart verification

Restart the staging service explicitly, then run:

```cmd
python agroq-lab\staging_acceptance_cli.py ^
  --mode verify ^
  --phase after_restart ^
  --base-url https://STAGING-DOMAIN ^
  --username STAGING-ADMIN ^
  --password STAGING-PASSWORD ^
  --state agroq-lab\results\controlled_beta\staging_state.json ^
  --output agroq-lab\results\controlled_beta\after_restart.json
```

## Redeployment verification

Deploy the same release candidate again while preserving the configured volume, then run:

```cmd
python agroq-lab\staging_acceptance_cli.py ^
  --mode verify ^
  --phase after_redeploy ^
  --base-url https://STAGING-DOMAIN ^
  --username STAGING-ADMIN ^
  --password STAGING-PASSWORD ^
  --state agroq-lab\results\controlled_beta\staging_state.json ^
  --output agroq-lab\results\controlled_beta\after_redeploy.json
```

## Human evidence

Capture and verify:

- Overview screenshot
- 3D Digital Acre screenshot
- Access & Community screenshot
- Quantum Lab screenshot
- Three-minute backup demonstration recording
- Current architecture summary
- Current limitations statement

## Acceptance decision

A named administrator records the final acceptance only after:

- all required checks pass;
- every demo-evidence item is verified;
- a verified backup exists;
- no latest scientific gate is failed;
- the rollback checkpoint is documented;
- release remains a manual administrator action.
