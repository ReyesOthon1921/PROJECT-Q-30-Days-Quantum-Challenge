# Operator Workflow

## Immediate local capability

After installation and restart:

```text
http://127.0.0.1:5000/admin/notifications
```

The page can be opened from a phone only when the Flask server is intentionally bound to
the local network and the phone is on the same network. Local-network exposure must use a
strong secret key, debug off, and an appropriate firewall rule.

## External delivery worker

Run once:

```bat
..\.venv-agroq\Scripts\python.exe scripts\run_notification_worker.py --once
```

Run continuously:

```bat
..\.venv-agroq\Scripts\python.exe scripts\run_notification_worker.py --interval 10
```

## Email environment variables

```text
AGROQ_SMTP_HOST=
AGROQ_SMTP_PORT=587
AGROQ_SMTP_USERNAME=
AGROQ_SMTP_PASSWORD=
AGROQ_SMTP_FROM=
AGROQ_SMTP_SSL=false
```

Do not commit SMTP passwords.

## HTTPS webhook

```text
AGROQ_ADMIN_WEBHOOK_URL=https://...
```

The URL is read from the environment and is not displayed in the administrator page.

## Web Push

Install optional dependencies:

```bat
..\.venv-agroq\Scripts\python.exe -m pip install -r requirements-notifications.txt
```

Generate VAPID keys:

```bat
..\.venv-agroq\Scripts\python.exe scripts\generate_vapid_keys.py
```

Load the generated private environment values into the deployed service. Do not commit
the generated file. Web Push should be enabled only on an HTTPS deployment.
