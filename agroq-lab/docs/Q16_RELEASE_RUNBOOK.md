# AgroQ Q16 Release Runbook

## Purpose

Q16 establishes release candidacy. It does not automatically deploy or promote a remote service.

## Local release gate

From the repository root:

```cmd
set AGROQ_DEPLOYMENT_MODE=staging
set AGROQ_DEBUG=false
set AGROQ_SECRET_KEY=replace-with-a-long-nondefault-secret
set AGROQ_ADMIN_USERNAME=q16admin
set AGROQ_ADMIN_PASSWORD=replace-with-a-long-nondefault-password
set WEB_CONCURRENCY=1

python agroq-lab\release_preflight.py --isolated --run-tests --run-build
```

The command must report:

```text
Q16 preflight passed: True
```

## Required local evidence

- Complete pytest suite passes.
- Q16 API and release-readiness tests pass.
- Vite production build passes.
- Git diff validation passes.
- Q16 preflight report passes.
- Release manifest is generated.
- Working tree is clean after commit.
- Local and remote branch heads match.

## SQLite deployment boundary

The beta deployment uses SQLite. Use one application worker:

```text
WEB_CONCURRENCY=1
```

Multiple application workers or replicas must not write to the same SQLite file.

## Storage requirement

Before storing real operational records, verify that the deployment provider preserves:

```text
AGROQ_DB_PATH
AGROQ_BACKUP_DIR
```

across rebuilds, restarts, and replacement deployments. A configured filesystem path alone does not prove provider-level persistence.

## Staging deployment

Remote staging begins only after an operator explicitly triggers deployment.

1. Record the release commit and release-candidate tag.
2. Create and verify a database backup.
3. Trigger the staging deployment.
4. Wait for the service health check to pass.
5. Run:

```cmd
python agroq-lab\staging_smoke.py ^
  --base-url https://STAGING-DOMAIN ^
  --output agroq-lab\results\release\q16\staging_smoke.json
```

6. Restart the service once.
7. Confirm the database, quantum registry, Q14 validation history, Q15 lifecycle records, and verified backup remain available.
8. Sign in and complete one controlled workflow:
   - open Q14 validation;
   - verify a frozen dataset;
   - replay a completed run;
   - open Q15 research operations;
   - review the evidence package;
   - confirm release remains manual.
9. Record screenshots, timestamps, service identifier, and smoke-test report.

## Production promotion

Production promotion is a separate decision.

Do not promote until:

- staging smoke passes;
- restart persistence passes;
- authenticated workflow review passes;
- rollback checkpoint is documented;
- no current scientific gate is failed;
- release notes and limitations are approved;
- a named operator authorizes promotion.
