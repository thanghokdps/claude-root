---
model: opus
effort: high
name: api-endpoint
description: Adds or changes a backend HTTP endpoint (Next.js route handler, Express/Hono, FastAPI) the way the repo already builds them. It covers the request/response schema, session auth, a permission check on the specific resource, a thin handler calling a service and repository, stable error codes, and the route test matrix (200, 400, 401, 404 for another user's resource). Use when the user asks for a new API route or endpoint, to change what an endpoint accepts or returns, or to fix an endpoint that leaks data or returns the wrong status.
when_to_use: new API endpoint, "thêm API endpoint", "viết API cho", REST route, route handler, controller, CRUD API, endpoint returns 500 instead of 400, endpoint shows another user's data, change request or response shape
---

# api-endpoint

**Invoke:** `/api-endpoint <method> <path> — what it does`

Rules: `api-contract.md`, `data-access.md` and `app-structure.md` from core (in `~/.claude/rules/`); on Python, `${CLAUDE_PLUGIN_ROOT}/rules/python.md` and `${CLAUDE_PLUGIN_ROOT}/rules/fastapi.md`. An agent tool is not an endpoint: use `/agent-tool` (ai, if installed).

---

## Step 1 — Detect how this repo builds endpoints

Find the existing pieces before writing any. **Reuse them**, because a second error wrapper or auth helper is a defect:

| Piece | Look for |
|-------|----------|
| Route location and style | `app/api/**/route.ts` (Next), `routes/` + `router.` (Express/Hono), `APIRouter` (FastAPI) |
| Wrapper and errors | `route(`, `HttpError`, `errorHandler`, `HTTPException`, exception middleware |
| Auth | `requireUser`, `getSession`, `Depends(get_current_user)`, auth middleware |
| Validation | `parseJson`, `z.object`, pydantic models |
| Aggregate | `server/<aggregate>/{schema,repository,service}.ts` or `app/<domain>/` |
| Test helpers | the route test helpers (`signInAs`, `request`, `params`), the test DB (PGlite, testcontainers, test client) |

Read one existing endpoint and its test end to end, and copy its shape.

**Done when:** each row names a file path, or "none" with the grep that found nothing. Missing auth or an error wrapper → build it once in the shared place (`server/http.ts`) as its own step, and ask first if it touches auth.

## Step 2 — Contract and failing tests

1. Request and response schema in `server/<aggregate>/schema.ts` (or the repo's place), exported for the client. The response is an explicit DTO, not the DB row.
2. Write the route test first, on the real test DB with only the session mocked:
   - 200 with the response shape, for the caller's own resource
   - 400 for a malformed body or query (and an invalid id format, if ids are typed)
   - 401 without a session
   - 404 for another user's resource. Seed two users, and test every method on the path.
   - 403 for a role that may not, 409/422/429 when the endpoint has those rules
3. A breaking change to an existing contract (rename, remove, retype) → stop and ask. Prefer an additive field or a new endpoint.

**Done when:** the tests exist and fail for the right reason (missing route or behaviour, not a typo).

## Step 3 — Implement, thin

- The handler is auth → validate → service/repository → DTO, inside the repo's error wrapper. No SQL and no business rule in the handler.
- Data reads and writes go through repository functions that take the owner (`/db-change` when a table, column or query is new).
- Composition across aggregates, quotas and side effects go in `service.ts`. Pure rules go in their own module with unit tests.
- Lists: limit with a server maximum, a stable sort, and cursor or offset.

**Done when:** the Step 2 tests pass, plus typecheck and lint.

## Step 4 — Prove it

Call the endpoint on the running dev server with a real session, once on your own resource and once on another user's. Show the status codes and the response body (`curl -i` or the browser). Update the repo's entry-points doc if it lists routes.

**Done when:** both calls show the expected status, with the output pasted.

---

Hand-offs: new table or query → `/db-change` · the frontend that calls it → `/ui-feature` (frontend, if installed) · auth or permission model changes → high-risk lane (`/coordinator`) · done → `/verify-done` → `/review-checklist` → `/docs-sync` so the route lands in `entry-points.md` (skip when `/feature` called this skill; it syncs once for the whole feature).
