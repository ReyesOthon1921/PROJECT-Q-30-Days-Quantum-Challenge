# Q17 Render Staging Blueprint

`render.staging.yaml` defines two separate staging services:

1. `agroq-controlled-beta-backend`
2. `agroq-controlled-beta-frontend`

The frontend service builds the Vite application and uses Nginx as a same-origin proxy to the backend over Render's private service network.

## Persistence boundary

The backend Blueprint includes a persistent disk mounted at `/var/data`:

```text
AGROQ_DB_PATH=/var/data/agroq.db
AGROQ_BACKUP_DIR=/var/data/backups
WEB_CONCURRENCY=1
```

The backend uses a paid `starter` plan because persistent disks are not available on the free web-service plan. The Blueprint is configuration only and does not create or charge for resources until an operator explicitly creates/syncs it in Render.

## Deployment boundary

Both services use:

```text
autoDeployTrigger: off
```

A commit or tag push does not trigger staging deployment. An operator must explicitly create or sync the Blueprint and start the deployment.

## Validation

After deployment:

1. run the Q17 prepare command;
2. restart the backend and run the after-restart verification;
3. redeploy the backend and run the after-redeploy verification;
4. complete human screenshot and workflow evidence;
5. accept staging only after every blocker is cleared.
