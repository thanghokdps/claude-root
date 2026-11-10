# backend

Role pack for the server side: the `backend-engineer` agent that `/feature`, `/ticket` and `/fix-bug` dispatch schema, endpoint and integration slices to, the three skills it runs, and the Python / FastAPI / NestJS / Hono / Cloudflare Workers / Better Auth / Prisma / Drizzle rules it reads on demand. Off by default; core's `repo-profile` hook turns it on in a repo with a server framework (Next.js route handlers, Express, Hono, NestJS, FastAPI, Django, Flask), a Cloudflare Worker (`wrangler` or a `wrangler.*` config), Firebase (`firebase.json`, `firestore.rules` or `firebase-admin`), an ORM or migration tool (Prisma, Drizzle, Alembic), Go or Rust.

**For:** backend developers, and every `/feature` run that includes a table, an endpoint or a third-party API.

## Agent

`agents/backend-engineer.md` (sonnet) builds exactly one slice from the supervisor's brief — aggregate, contract, files, test, done check — by running the skills below, and reports in three lines. Authentication and owner-scoped queries are hard gates it stops on rather than weakens. The screen that calls the endpoint, agent tools (`agent` pack) and destructive migrations (`/write-migration`) are not its job.

## Skills

| Skill           | Use it when                                                                                                                                                                                        | Example prompt                           |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `/api-endpoint` | A new or changed backend route: schema shared with the frontend, session auth, permission on the specific resource, thin handler, stable error codes, the 200/400/401/404 test matrix              | "thêm API endpoint tạo đơn hàng"         |
| `/db-change`    | A new table, column, index or relation, or a slow or leaking query (Drizzle, Prisma, Alembic). ERD and schema first, reviewed migration, owner-scoped repository functions, tests on a real engine | "query trả dữ liệu của user khác"        |
| `/api-client`   | The backend must call a third party from its OpenAPI spec, docs or curl: typed client, credentials from env, timeouts, retries for idempotent reads only, webhooks, mocks                          | "tích hợp API thanh toán từ swagger này" |

## Rules

`rules/python.md`, `rules/fastapi.md`, `rules/nestjs.md` (modular monolith, guard → zod pipe → service, one exception filter, one `PermissionService` for REST and Socket.IO, Fastify, pg-boss, nestjs-pino, Vitest on a real Postgres), `rules/prisma.md`, `rules/drizzle.md` (schema as source, generated add-only migrations, `migrate` not `push` on shared databases, one pool, parameterised `sql`, FTS via raw SQL; on D1 `db.batch`, `wrangler d1 migrations apply`, FTS5), `rules/hono.md` (sub-app per aggregate, session → zValidator → service, one `onError`, `app.request` tests), `rules/cloudflare-workers.md` (per-environment bindings, `compatibility_date`, D1 limits, Durable Objects with Hibernation, Queues ack and idempotency, R2 presign + finalize, `@cloudflare/vitest-plugin`), `rules/better-auth.md` (no cookie cache, idle vs absolute expiry, Google `hd` and `sub`, revoke on deactivation), `rules/firestore.md` (REST from Workers bypasses Security Rules so the server scopes every query, atomic `commit`, no hot counter documents, cost per listener, rules tests on the emulator), `rules/firebase-auth.md` (ID tokens verified with `jose`, domain and `email_verified` checked server-side, session caps and deactivation enforced by the server, service-account access tokens), `rules/fcm.md` (tokens pruned on `UNREGISTERED`, sends from an idempotent Queue consumer, retry by error code) — read by the agent and the skills when the repo uses them, never always-loaded. `api-contract.md`, `data-access.md` and `security.md` stay in core, since every role reads them.

## Install

```text
/plugin install backend@harness
```

The marketplace must be added first: see the [root README](../../README.md#quickstart).
