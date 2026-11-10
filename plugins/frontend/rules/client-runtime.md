---
paths:
  - "**/stores/**/*.ts"
  - "**/outbox/**/*.ts"
  - "**/realtime/**/*.ts"
  - "**/firebase-messaging-sw.js"
---

# Client runtime rules (Zustand state, offline outbox, Effect flows, web push)

For a SPA that keeps working through dropped connections. Server data stays in TanStack Query (`tanstack.md`); this rule is for what the client owns. Claims cite zustand.docs.pmnd.rs, effect.website and firebase.google.com (read 2026-11-10).

## Zustand: client-owned state only

- A Zustand store holds UI state nothing on the server owns: the outbox, open panels, the composer's draft per conversation. Never a copy of server data that TanStack Query already caches.
- One store per concern, read with selectors (`useOutbox(s => s.pending(id))`) so a component re-renders only for its slice.
- State that must survive a reload uses `persist` with a unique `name`, `partialize` to persist only what is needed, and a `version` plus `migrate` from the first release. A version change with no `migrate` drops the stored state ([persisting store data](https://zustand.docs.pmnd.rs/reference/integrations/persisting-store-data)). An IndexedDB storage (through `createJSONStorage` with async `getItem` / `setItem` / `removeItem`) hydrates asynchronously, so wait for hydration before reading.
- Never persist a token, a private message body for longer than its send, or anything that identifies another person beyond ids.

## Outbox: unsent messages

- Every send gets a client id (UUID) before it leaves the composer. The outbox entry, the optimistic cache entry and the server write all use it, so a retry or a reconnect never creates a second message.
- An entry moves `pending → sending → sent | failed`. `failed` shows "Not sent" with Retry; the entry stays until it is sent or the person discards it.
- On reconnect the outbox flushes in creation order per conversation, after the catch-up fetch, so the reader never sees their own message out of order.
- Sign-out clears the outbox and every persisted store.

## Effect flows (when the repo uses `effect`)

- Send, retry and reconnect are Effects with typed failures (`Data.TaggedError`): `Offline`, `Unauthorized`, `RateLimited`, `Rejected` ([expected errors](https://effect.website/docs/error-management/expected-errors/)). The UI maps each tag to one state, so there is no catch-all "something went wrong".
- Reconnect backs off with `Effect.retry` and `Schedule.exponential` capped by `Schedule.recurs`. `Unauthorized` and `Rejected` are never retried ([retrying](https://effect.website/docs/error-management/retrying/), [schedules](https://effect.website/docs/scheduling/built-in-schedules/)).
- Effects run at the edge of React (an event handler, a store action) with `Effect.runPromise`, never inside render ([running effects](https://effect.website/docs/getting-started/running-effects/)).

## Web push on the client

- `firebase-messaging-sw.js` sits at the site root and calls `onBackgroundMessage`. The page gets its token with `getToken` and the VAPID key ([receive messages](https://firebase.google.com/docs/cloud-messaging/js/receive)). The rest of delivery is the backend pack's `rules/fcm.md`, if installed.
- Ask for permission after the first DM or mention, never on load. A refused permission is remembered and not asked again in the same session.
- No notification fires for the conversation the person has open and focused, and only one fires across tabs.

## Tests

- Store tests: persist round-trip, `migrate` from the previous version, sign-out clears.
- Outbox tests: offline send → reconnect → exactly one message, in order; a `Rejected` send stays failed with Retry.
