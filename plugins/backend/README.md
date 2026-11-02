# backend

Role pack for the server side: the `backend-engineer` agent that `/feature`, `/ticket` and `/fix-bug` dispatch schema, endpoint and integration slices to, the three skills it runs, and the Python / FastAPI / Prisma rules it reads on demand. Off by default; core's `repo-profile` hook turns it on in a repo with a server framework (Next.js route handlers, Express, Hono, NestJS, FastAPI, Django, Flask), an ORM or migration tool (Prisma, Drizzle, Alembic), Go or Rust.

**For:** backend developers, and every `/feature` run that includes a table, an endpoint or a third-party API.

## Agent

`agents/backend-engineer.md` (sonnet) builds exactly one slice from the supervisor's brief — aggregate, contract, files, test, done check — by running the skills below, and reports in three lines. Authentication and owner-scoped queries are hard gates it stops on rather than weakens. The screen that calls the endpoint, agent tools (`agent` pack) and destructive migrations (`/write-migration`) are not its job.

## Skills

| Skill | Use it when | Example prompt |
|---|---|---|
| `/api-endpoint` | A new or changed backend route: schema shared with the frontend, session auth, permission on the specific resource, thin handler, stable error codes, the 200/400/401/404 test matrix | "thêm API endpoint tạo đơn hàng" |
| `/db-change` | A new table, column, index or relation, or a slow or leaking query (Drizzle, Prisma, Alembic). ERD and schema first, reviewed migration, owner-scoped repository functions, tests on a real engine | "query trả dữ liệu của user khác" |
| `/api-client` | The backend must call a third party from its OpenAPI spec, docs or curl: typed client, credentials from env, timeouts, retries for idempotent reads only, webhooks, mocks | "tích hợp API thanh toán từ swagger này" |

## Rules

`rules/python.md`, `rules/fastapi.md`, `rules/prisma.md` — read by the agent and the skills when the repo uses them, never always-loaded. `api-contract.md`, `data-access.md` and `security.md` stay in core, since every role reads them.
