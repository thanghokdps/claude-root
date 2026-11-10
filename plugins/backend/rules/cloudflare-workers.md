---
paths:
  - "**/wrangler.jsonc"
  - "**/wrangler.json"
  - "**/wrangler.toml"
  - "**/worker-configuration.d.ts"
---

# Cloudflare Workers rules (Workers, D1, Durable Objects, Queues, R2, rate limits, email, Access, observability)

Adds only what is Workers-specific. Routing is in `hono.md`, queries in `drizzle.md` § SQLite and Cloudflare D1, the contract and owner scoping in core's `api-contract.md` and `data-access.md`. Claims cite developers.cloudflare.com (read 2026-11-10). Cloudflare's `workers-best-practices`, `durable-objects` and `wrangler` skills, if installed, go deeper.

## Config and environments

- `wrangler.jsonc` is the one source for the Worker's bindings, routes and environments. Types come from `wrangler types` and are never written by hand ([vitest: first test](https://developers.cloudflare.com/workers/testing/vitest-integration/write-your-first-test/)).
- Set `compatibility_date` to the day the project starts. Bump it on purpose: read the [compatibility flags](https://developers.cloudflare.com/workers/configuration/compatibility-flags/) it turns on, then test it through dev and staging. The new date applies at the next `wrangler deploy` ([compatibility dates](https://developers.cloudflare.com/workers/configuration/compatibility-dates/)).
- Bindings, vars and secrets are not inherited: declare every D1, R2, Queue and Durable Object binding again under each `env.<name>`, and set secrets per environment ([environments](https://developers.cloudflare.com/workers/wrangler/environments/)). A binding left out of an environment means that Worker silently has none. Every environment gets its own database, bucket and queues. They never share one with production.
- Deploy and run with `--env <name>` (or `CLOUDFLARE_ENV`; `--env` wins) ([environments](https://developers.cloudflare.com/workers/wrangler/environments/)). A release promotes the build that passed staging; it is never rebuilt for production.
- A single-page app is served by the same Worker from Static Assets: `assets.directory` plus `"not_found_handling": "single-page-application"` ([SPA routing](https://developers.cloudflare.com/workers/static-assets/routing/single-page-application/)). Never put a secret in the asset build: everything in it is public.

## D1

- Each database is single-threaded and runs one query at a time, so at 1 ms per query it tops out near 1,000 queries per second ([D1 limits](https://developers.cloudflare.com/d1/platform/limits/)). Any slow query, search included, delays every other read and write. Load-test the slowest query while writes are running, before the milestone that depends on it.
- A database holds at most 10 GB, and the limit "cannot be further increased" ([D1 limits](https://developers.cloudflare.com/d1/platform/limits/)). Alert on storage well below the cap, and set a retention default. Plan the split (a second database, or one per tenant) before the alert fires.
- A multi-statement write goes in one `batch()`: a batch is a SQL transaction and rolls back as a whole ([D1 database API](https://developers.cloudflare.com/d1/worker-api/d1-database/)). A batch counts as one query against the per-invocation limit ([D1 limits](https://developers.cloudflare.com/d1/platform/limits/)).

## Durable Objects and WebSockets

- Accept sockets with `this.ctx.acceptWebSocket(ws)` (the Hibernation API), never `ws.accept()`, so an idle object stops billing duration while clients stay connected ([DO WebSockets](https://developers.cloudflare.com/durable-objects/best-practices/websockets/)).
- After hibernation, in-memory state is gone and the constructor runs again. Keep the constructor light, and keep per-socket state (user id, session id) in `ws.serializeAttachment()` ([DO WebSockets](https://developers.cloudflare.com/durable-objects/best-practices/websockets/)). A field set only in `webSocketMessage` is lost on the next wake.
- One object has a soft limit of 1,000 requests per second ([DO limits](https://developers.cloudflare.com/durable-objects/platform/limits/)). Shard by the natural key (one object per user, per conversation, per workspace) and never route the whole app through one global object.
- The Worker authenticates the upgrade request and checks the session before calling `stub.fetch()`. The object trusts only the identity the Worker passes, never one the client sends. Ending a session or deactivating a person closes that person's sockets through their object.
- A deploy disconnects every socket. The client reconnects with backoff and catches up from the last event id it saw, so no event depends on the socket staying open.

## Queues and Cron Triggers

- Call `msg.ack()` on each message once it is handled, and `msg.retry()` on one that failed. A throw from the consumer redelivers the entire batch ([batching and retries](https://developers.cloudflare.com/queues/configuration/batching-retries/)). Make every consumer idempotent: key the side effect (a push sent, a row written) on the message's own id, so a redelivery repeats nothing.
- A cron job that deletes or rewrites rows (retention, orphan cleanup) works in bounded batches and records where it stopped, so a timeout resumes instead of starting over.

## R2

- The R2 binding cannot presign. Sign uploads with `aws4fetch` or the AWS SDK v3 ([presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)). Sign the content type and length, and expire in minutes, not the 7-day maximum.
- An upload is not usable until a finalize call reads its first bytes, checks the real type and size, and only then marks it ready. Downloads go through the Worker after the permission check, never through a public bucket URL.

## Rate limits, email, Access, observability

- The Rate Limiting binding (`ratelimits: [{ name, namespace_id, simple: { limit, period } }]`, period 10 or 60 seconds, Wrangler 4.36.0+) is per Cloudflare location, approximate and eventually consistent ([rate limit binding](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/)). Use it for flood control keyed on the user id (not the IP alone, which an office shares). A limit that must be exact, such as sign-in attempts, counts in a Durable Object instead.
- Email from a Worker uses the Email Service binding: `send_email: [{ name: "EMAIL" }]`, then `env.EMAIL.send({ to, from, subject, text })`, which throws with a `code` (for example `E_SENDER_NOT_VERIFIED`) ([Workers API](https://developers.cloudflare.com/email-service/api/send-emails/workers-api/)). Email Sending is in beta, and sending to any recipient needs Workers Paid ([Email Service](https://developers.cloudflare.com/email-service/)). Send from a Queue consumer, never inline in a request.
- Staging and preview URLs are public by default ([previews](https://developers.cloudflare.com/workers/configuration/previews/)). Put them behind Cloudflare Access, and in the Worker verify the `Cf-Access-Jwt-Assertion` header with `jose` against `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs`, checking `iss` (the team domain) and `aud` (the application's AUD tag) ([validate the Access JWT](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/)). Access is an outer gate. The app's own sign-in still runs behind it.
- Turn on `observability: { enabled: true, head_sampling_rate }` for logs and `observability.traces.enabled: true` for traces; `enabled` alone gives logs only, and traces are kept 7 days ([Workers Logs](https://developers.cloudflare.com/workers/observability/logs/workers-logs/), [traces](https://developers.cloudflare.com/workers/observability/traces/)). Log ids and codes, never message bodies, tokens or emails.

## Tests

- Tests run inside the Workers runtime with `@cloudflare/vitest-plugin`. It replaces `@cloudflare/vitest-pool-workers`; migrate an older repo with `npx @cloudflare/codemods vitest:pool-workers-to-vitest-plugin` ([migrate to Vitest plugin](https://developers.cloudflare.com/workers/testing/vitest-integration/migration-guides/migrate-to-vitest-plugin/)).
- Read bindings from `env` in `cloudflare:workers`, and drive the whole Worker with `exports.default.fetch()` for route tests ([vitest: first test](https://developers.cloudflare.com/workers/testing/vitest-integration/write-your-first-test/)). Apply the committed D1 migrations to the test database first: a test on a hand-made schema proves nothing about production.
- Durable Object and Queue behaviour (a socket closed on deactivation, a redelivered message that sends nothing twice) gets its own test. It is the part a route test never reaches.
