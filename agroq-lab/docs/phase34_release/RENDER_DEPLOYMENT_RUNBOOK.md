# AgroQ Render Live-Deployment Runbook

## Release target

The first target is a **public demonstration deployment** on Render using one Docker web
service. Flask serves:

- the manual-first operations application
- authentication and administrator pages
- the access/community portal
- the notification center
- the sequence APIs
- the professional React interface at `/app/`

This same-origin design avoids cross-origin session-cookie problems.

## Before committing

Run from the repository root:

```bat
git branch --show-current
git status --short
git diff --stat
```

Do not stage:

```text
.env
.env.*
instance/
backups/
node_modules/
dist/
*.db
*.sqlite
*.sqlite3
AgroQ_Private/
```

## Build the professional interface with the deployment base path

```bat
cd agroq-lab\investor-ui
npm run build -- --base=/app/
cd ..\..
```

## Run release preflight

```bat
.\.venv-agroq\Scripts\python.exe agroq-lab\scripts\production_preflight.py
```

Required result:

```text
RELEASE PREFLIGHT: PASS
```

## Stage the release

```bat
git add agroq-lab render.yaml deployment
git status --short
git diff --cached --stat
```

Review the staged files before committing.

## Commit and push

```bat
git commit -m "Deploy AgroQ controlled public demo"
git push -u origin phase3-6-investor-prototype
```

## Create the Render Blueprint

1. Open the Render Dashboard.
2. Choose **New → Blueprint**.
3. Connect `ReyesOthon1921/PROJECT-Q-30-Days-Quantum-Challenge`.
4. Select the repository's `render.yaml`.
5. Enter the values requested for:
   - `AGROQ_ADMIN_PASSWORD`
   - `AGROQ_NCBI_EMAIL`
6. Confirm the service name and Free instance.
7. Apply the Blueprint.
8. Watch the build logs.
9. Confirm `/healthz` returns HTTP 200.

## Live verification

Visit:

```text
https://<service-name>.onrender.com/healthz
https://<service-name>.onrender.com/login
https://<service-name>.onrender.com/admin/notifications
https://<service-name>.onrender.com/app/
```

Verify:

- health check passes
- administrator login works
- notification center loads
- professional interface loads
- three experiment records appear
- in-app test notification works
- sequence search reaches NCBI
- field mode remains locked
- no private local files are exposed

## Free-demo limitation

A free Render web service spins down after inactivity and has an ephemeral filesystem.
Local SQLite changes can disappear after spin-down, restart, or redeploy. Use the free
configuration for a public demonstration only.

For a controlled beta with durable accounts, notifications, and experiment records, use
`deployment/render.persistent.yaml` with a paid service and persistent disk, or migrate
the application to a managed relational database.
