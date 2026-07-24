# Professional and Research Basis

The design uses a durable event/outbox pattern:

```text
Authentication or access event
        ↓
Durable event record and audit link
        ↓
Preference and channel routing
        ↓
In-app / email / HTTPS webhook / encrypted Web Push
        ↓
Delivery status and administrator acknowledgement
```

## Standards and research

1. W3C Push API, latest published Working Draft (2025).
   The application server sends a push message through a push service; a service worker
   receives it even when the web application is inactive.

2. IETF RFC 8030, Generic Event Delivery Using HTTP Push.

3. IETF RFC 8291, Message Encryption for Web Push.

4. IETF RFC 8292, Voluntary Application Server Identification (VAPID).
   VAPID binds subscriptions to an application-server identity using signed tokens.

5. NIST SP 800-63B session-management guidance.
   Administrator sessions need inactivity and overall timeout controls, with
   reauthentication for sensitive actions.

6. NIST SP 800-92, Guide to Computer Security Log Management.
   Security events should be generated, transmitted, stored, reviewed, and retained
   through a deliberate log-management process.

7. Nguyen, Nguyen, and Pham, “Publish-Subscribe Framework for Event Management in
   IoT-based Applications” (2018).
   The paper demonstrates an event-monitoring design that routes IoT events to
   subscribers through internet and messaging channels.

## AgroQ interpretation

AgroQ keeps the durable in-app record as the source of truth. External messaging is a
delivery adapter. A channel failure never deletes the source event. Passwords, PINs,
tokens, cookies, authorization headers, and API keys are redacted before metadata is
stored or sent.
