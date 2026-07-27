# AgroQ Lead Notification and Follow-up Workflow

## Immediate founder notifications

The existing AgroQ notification center is upgraded so signup-related audit
events are dispatched immediately. The founder receives:

- an in-app notification;
- an email when SMTP is configured;
- a delivery status of pending, sent, failed, or skipped.

The notification email includes sanitized submission metadata, including the
applicant's name, email, organization, request type, and message when available.

## Founder inbox

The default founder notification address is:

`reyesothon1921@gmail.com`

It can be replaced with the Render environment variable:

`AGROQ_NOTIFICATION_EMAIL`

## Follow-up status workflow

Every access request, beta reservation, and available Founding Grower
reservation receives:

- status;
- priority;
- last-contacted timestamp;
- next-follow-up date;
- contact method;
- follow-up notes;
- complete status history.

Statuses:

1. New
2. Reviewing
3. Contacted
4. Meeting scheduled
5. Proposal sent
6. Waiting on customer
7. Onboarded
8. Closed
9. Not a fit

The administrator page is:

`/admin/leads`

The notification center remains:

`/admin/notifications`

## Required Render email settings

- `AGROQ_NOTIFICATION_EMAIL=reyesothon1921@gmail.com`
- `AGROQ_SMTP_HOST`
- `AGROQ_SMTP_PORT`
- `AGROQ_SMTP_USERNAME`
- `AGROQ_SMTP_PASSWORD`
- `AGROQ_SMTP_FROM`
- `AGROQ_SMTP_SSL`

Keep passwords only in Render environment variables.
