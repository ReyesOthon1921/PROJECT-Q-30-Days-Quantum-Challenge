# AgroQ Q16 Rollback Runbook

## Rollback principle

Preserve evidence first. Never erase the active database or Q14/Q15 history to make a failed deployment appear successful.

## Before deployment

Record:

- release commit;
- release-candidate tag;
- current successful deployment identifier;
- database path;
- backup directory;
- latest verified backup filename and SHA-256;
- SQLite integrity result;
- staging smoke result.

## Application rollback

1. Stop or block new writes.
2. Preserve the current database file.
3. Roll the application image or commit back to the previous successful release.
4. Keep the persistent storage attached.
5. Run `/healthz`.
6. Sign in and verify:
   - access controls;
   - experiment registry;
   - Q14 validation history;
   - Q15 lifecycle history;
   - evidence bundles;
   - audit events.
7. Record the rollback reason and operator.

## Database rollback

1. Stop all writes.
2. Copy the current database to a forensic preservation filename.
3. Select a verified backup.
4. Restore the backup to a separate temporary path.
5. Run `PRAGMA integrity_check`.
6. Start a temporary application instance against the recovered copy.
7. Verify login, audit records, quantum experiments, validation events, research operations, and evidence bundles.
8. Replace the active database only after verification.
9. Keep the damaged database and recovery report.

## Frontend rollback

1. Restore the previous successful frontend build.
2. Keep the backend and database unchanged.
3. Verify `/app/`, login navigation, Q14, Q15, Q16, and acknowledgments.
4. Record the browser, timestamp, and deployment identifier.

## Rollback failure

When rollback verification fails:

- keep writes disabled;
- preserve all database and log files;
- do not retry destructive migrations;
- escalate for manual database recovery;
- document every command and result.
