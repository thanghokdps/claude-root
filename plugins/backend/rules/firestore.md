---
paths:
  - "**/firestore.rules"
  - "**/firebase.json"
  - "**/firestore/**/*.ts"
  - "**/repositories/**/*.ts"
---

# Firestore rules (data on Firestore, server on Workers or Node)

Adds only what is Firestore-specific. Owner scoping is core's `data-access.md`; sign-in is `firebase-auth.md`; Workers config is `cloudflare-workers.md`. Claims cite firebase.google.com and docs.cloud.google.com (read 2026-11-10).

## Two ways in, two rule sets

- The Firebase Admin SDK needs Node, so a Worker talks to Firestore over the REST API at `https://firestore.googleapis.com/v1/projects/<p>/databases/(default)/documents` ([REST API](https://firebase.google.com/docs/firestore/use-rest-api)). A server that runs Node (a Container, Cloud Run) may use the Admin SDK instead. Pick one per service, never both.
- A request made with a service-account OAuth token (scope `https://www.googleapis.com/auth/datastore`) is authorised by IAM and **bypasses Security Rules**. A request made with a user's Firebase ID token is checked against the Rules ([REST API](https://firebase.google.com/docs/firestore/use-rest-api); "the server client libraries bypass all Cloud Firestore Security Rules", [rules get started](https://firebase.google.com/docs/firestore/security/get-started)).
- So the server's repository functions do their own permission and owner check on every read and write, exactly as core's `data-access.md` asks of SQL. The Rules protect the client SDK path (realtime listeners), not the server. Write down in the repo which collections the client may read directly and which only the server touches.
- The service-account key is a secret of the Worker (`wrangler secret put`), one per environment, scoped to the roles it needs. The access token is minted from it with the JWT bearer flow (`firebase-auth.md` § Google access tokens) and cached until shortly before its 1-hour expiry.

## Writes

- A multi-document write goes through `documents:commit` (atomic) or `:beginTransaction` + `:commit` when it reads first ([REST reference](https://docs.cloud.google.com/firestore/docs/reference/rest)). `:batchWrite` is not atomic: use it only for independent writes such as a purge, and check every per-write status it returns.
- A document holds at most 1 MiB ([quotas](https://firebase.google.com/docs/firestore/quotas)). Messages, reactions and read markers are their own documents, never arrays that grow on a parent.
- Sequential document ids and high-rate monotonic fields (a timestamp written on every message) create hotspots; use auto ids ([best practices](https://firebase.google.com/docs/firestore/best-practices)). A per-conversation counter document incremented on every message is one hot document: do not order messages with it. Order by a server timestamp plus the auto id as tie-break, and load-test the write rate the busiest conversation needs; the docs give no per-document number, they say to test.
- A new collection with heavy traffic ramps by the 500/50/5 rule: at most 500 operations a second at first, then up 50% every 5 minutes ([best practices](https://firebase.google.com/docs/firestore/best-practices)). A backfill or import follows it.
- A retry of a client send must not write twice: the client sends its own message id and the server uses it as the document id (or checks it inside the transaction).

## Cost

- Every document read, write and delete is billed; a listener is billed a read for each document added or changed in its result set, and a reconnect after more than 30 minutes offline is billed as a new query (always, when offline persistence is off) ([pricing](https://firebase.google.com/docs/firestore/pricing)).
- Estimate the monthly cost from the expected messages, readers and listeners before the milestone that adds a listener, and keep the estimate in the repo's docs. A listener on a whole conversation history is a cost bug: listen to the latest page, page older messages with queries.

## Security Rules

- `firestore.rules` is code: reviewed, versioned with the app and deployed with it, never edited in the console.
- Every rule that grants client access has a unit test with `@firebase/rules-unit-testing` against the emulator: `initializeTestEnvironment()`, `assertSucceeds` for the member, `assertFails` for the outsider and the deactivated person, `clearFirestore()` between tests ([rules unit tests](https://firebase.google.com/docs/rules/unit-tests)). A rule change without a failing-then-passing test is not done.
- A rule never trusts a field the client wrote (`request.resource.data.role`); it reads membership from a document only the server writes.

## Local and tests

- Run Firestore and Auth in the Emulator Suite. `firebase emulators:exec "<test command>"` starts them, runs the tests and stops them, which suits CI ([emulator suite](https://firebase.google.com/docs/emulator-suite/install_and_configure)). Point the code at them with `FIRESTORE_EMULATOR_HOST=127.0.0.1:8080` and `FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099`, without a protocol ([Firestore](https://firebase.google.com/docs/emulator-suite/connect_firestore), [Auth](https://firebase.google.com/docs/emulator-suite/connect_auth)).
- Repository tests run on the emulator, never on a mock of the REST API and never on a shared project.
- A Firebase project shared with another product (Space) is shared data: a schema change, a rules change or a purge job there is high-risk, needs that team's review, and its rules tests run in both repos.
