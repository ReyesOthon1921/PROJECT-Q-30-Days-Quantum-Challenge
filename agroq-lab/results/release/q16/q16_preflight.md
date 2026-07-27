# AgroQ Q16 Release Preflight

- Generated: 2026-07-26T01:57:15+00:00
- Passed: YES

## git_repository

- Result: PASS
- Message: Git repository and working-tree state validated.

```json
{
  "branch": "phase3-6-investor-prototype",
  "head": "9ec5f2c7f08d8d7fe827c40a96bcb094dc0e07a9",
  "dirty": true,
  "status": "M agroq-lab/Dockerfile\n M agroq-lab/app.py\n M agroq-lab/investor-ui/src/components/QuantumRegistryWorkspace.jsx\n M agroq-lab/investor-ui/src/data/quantumApi.js\n M agroq-lab/investor-ui/src/quantum_registry.css\n M agroq-lab/investor-ui/src/styles.css\n M render.yaml\n?? .github/\n?? agroq-lab/docs/Q16_RELEASE_RUNBOOK.md\n?? agroq-lab/docs/Q16_ROLLBACK_RUNBOOK.md\n?? agroq-lab/docs/RESEARCH_MENTORS_AND_COLLABORATORS.md\n?? agroq-lab/investor-ui/src/components/ReleaseReadinessWorkspace.jsx\n?? agroq-lab/investor-ui/src/release_readiness.css\n?? agroq-lab/release_manifest.py\n?? agroq-lab/release_preflight.py\n?? agroq-lab/release_readiness.py\n?? agroq-lab/staging_smoke.py\n?? agroq-lab/tests/test_release_preflight.py\n?? agroq-lab/tests/test_release_readiness_api.py\n?? agroq-lab/tests/test_release_readiness_core.py\n?? agroq-lab/tests/test_research_mentor_acknowledgments.py\n?? agroq-lab/tests/test_staging_smoke.py",
  "allow_dirty": true
}
```

## python_dependencies

- Result: PASS
- Message: Required Python dependencies are importable.

```json
{
  "python": "3.13.2 (tags/v3.13.2:4f8bb39, Feb  4 2025, 15:23:48) [MSC v.1942 64 bit (AMD64)]",
  "missing": []
}
```

## environment_safety

- Result: PASS
- Message: Deployment environment avoids development defaults.

```json
{
  "deployment_mode": "staging",
  "debug": "false",
  "problems": []
}
```

## sqlite_single_worker

- Result: PASS
- Message: SQLite deployment is constrained to one application worker.

```json
{
  "render_workers": 1,
  "docker_single_worker": true,
  "problems": []
}
```

## storage_writable

- Result: PASS
- Message: Database and backup directories are writable.

```json
{
  "database_path": "C:\\Users\\reyes\\AppData\\Local\\Temp\\agroq-q16-preflight-33bslbtf\\instance\\agroq.db",
  "backup_path": "C:\\Users\\reyes\\AppData\\Local\\Temp\\agroq-q16-preflight-33bslbtf\\backups",
  "problems": []
}
```

## schema_and_database

- Result: PASS
- Message: Schema is idempotent, required tables exist, and SQLite is healthy.

```json
{
  "schema_path": "C:\\Users\\reyes\\QuantumResearch\\quantum-education-research-lab\\agroq-lab\\schema.sql",
  "database_path": "C:\\Users\\reyes\\AppData\\Local\\Temp\\agroq-q16-preflight-33bslbtf\\instance\\agroq.db",
  "schema_sha256": "278c7a8ee6758fa4465bc0602eca902b478b895e2500031902e2f0eaa8ed5510",
  "missing_tables": [],
  "integrity": "ok",
  "problems": []
}
```

## application_runtime

- Result: PASS
- Message: Health, authentication, quantum APIs, source seeding, and backup recovery passed.

```json
{
  "healthz_status": 200,
  "login_status": 302,
  "quantum_health_status": 200,
  "release_readiness_status": 200,
  "quantum_source_count": 16,
  "latest_failed_validations": 0,
  "approved_not_released": 0,
  "backup": {
    "backup_id": "AGQ-BACKUP-1785031035876811700",
    "filename": "agroq-20260726T015715Z-1785031035876843900.sqlite3",
    "status": "verified",
    "message": "ok",
    "size_bytes": 774144
  },
  "backup_recovery": {
    "passed": true,
    "message": "ok"
  },
  "problems": []
}
```
