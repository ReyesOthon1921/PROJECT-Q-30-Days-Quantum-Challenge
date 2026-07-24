# AgroQ Phase 3.3 — Mobile Administrator Notifications

## Implemented

- Administrator-only responsive notification center
- Durable SQLite notification event store
- Audit-event-to-notification trigger
- Successful sign-in notifications
- Failed sign-in notifications
- Signup/access/invitation/account/role/password activity notifications
- Sensitive field redaction
- Acknowledgement and unread counts
- Per-administrator delivery preferences
- Optional SMTP email adapter
- Optional HTTPS webhook adapter
- Optional encrypted Web Push adapter
- Push subscription management
- Background notification worker
- Delivery attempts and failure history
- Professional architecture schematic
- Unit tests

## Truth boundary

In-app notification records work locally.

External email and webhook delivery require provider configuration and the notification
worker. Background phone notifications require a reachable HTTPS deployment, VAPID keys,
a compatible browser, permission from the administrator, and the notification worker.
