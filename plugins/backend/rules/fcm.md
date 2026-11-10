---
paths:
  - "**/push/**/*.ts"
  - "**/notifications/**/*.ts"
  - "**/firebase-messaging-sw.js"
---

# Push notification rules (Firebase Cloud Messaging, sent from a Queue)

Who gets notified (mute, quiet hours, mentions) is product logic in the service; this rule covers delivery. The service-account token is `firebase-auth.md` § Google access tokens; Queue semantics are `cloudflare-workers.md` § Queues. Claims cite firebase.google.com (read 2026-11-10).

## Tokens

- The web client gets a registration token with `getToken(messaging, { vapidKey, serviceWorkerRegistration })`, and needs `firebase-messaging-sw.js`, which calls `onBackgroundMessage` to show a notification while the tab is closed ([receive messages](https://firebase.google.com/docs/cloud-messaging/js/receive), [messaging API](https://firebase.google.com/docs/reference/js/messaging_.md)).
- Ask for notification permission after a meaningful moment (the first DM or mention), never on page load.
- Store tokens per person and device with a last-seen date. A token with no connection for over a month is stale; delete a token as soon as a send returns `UNREGISTERED` (404), and prune stale ones on a schedule ([manage tokens](https://firebase.google.com/docs/cloud-messaging/manage-tokens)). Deactivating a person deletes their tokens.

## Sending

- The request path never calls FCM. It decides who to notify and enqueues one job per recipient; a Queue consumer sends. A slow or failing FCM never slows a message send.
- Send with HTTP v1: `POST https://fcm.googleapis.com/v1/projects/<p>/messages:send`, Bearer token with scope `https://www.googleapis.com/auth/firebase.messaging` ([HTTP v1](https://firebase.google.com/docs/cloud-messaging/send/v1-api)).
- Handle errors by code ([ErrorCode](https://firebase.google.com/docs/reference/fcm/rest/v1/ErrorCode)): `UNREGISTERED` → delete the token, ack; `INVALID_ARGUMENT` → a bug in the payload, ack and log; `QUOTA_EXCEEDED` (429), `UNAVAILABLE` (503), `INTERNAL` (500) → `msg.retry()` with exponential backoff, honouring `Retry-After`.
- The job id is the notification's own id (message id + recipient). The consumer records it before sending, so a redelivered batch sends nothing twice; exhausted retries go to the dead-letter queue, which someone watches.
- Quiet hours and mute are checked when the job runs, not only when it was enqueued: a person may have muted in between. A held notification is never lost: badges and unread counts still update.
- The payload carries ids and a short preview at most; never the body of a private message or a file link that works without a permission check.

## Tests

- Consumer tests: success, `UNREGISTERED` deletes the token, 429 retries, a redelivered message sends once, quiet hours hold, mute blocks `@channel` but not a direct mention.
- The service worker's background notification is checked by hand on each supported browser before a release that touches it; record the result in the release notes.
