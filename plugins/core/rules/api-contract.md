---
paths:
  - "**/app/api/**"
  - "**/routes/**"
  - "**/routers/**"
  - "**/server/**"
  - "**/controllers/**"
  - "**/api/**/*.py"
---

# HTTP API contract (backend)

## Every handler, in this order

1. **Authenticate**: the session or token is verified on the server, giving a user or a 401. Identity never comes from the body, query or a client header.
2. **Validate** the input at the boundary with a schema (zod, pydantic): body, params, query and headers that matter. Bad input is a 400 with a code, never a 500.
3. **Authorise on the specific resource**: load it scoped by the caller (`where id = ? and owner_id = ?`). Not found and not yours both answer **404**, so the API never confirms another user's ids exist. Role checks are 403.
4. **Call the service or repository.** The handler holds no SQL and no business rules.
5. **Respond with an explicit DTO**, never a raw DB row (hidden columns, internal ids, password hashes).

## Errors

- One wrapper per app turns thrown errors into `{ "error": "<code>" }` with the right status: 400, 401, 403, 404, 409 conflict, 422, 429. Anything else is a 500 `internal`, logged with the path and no stack trace or secret in the response.
- Error codes are stable strings (`not_found`, `invalid_body`, `quota_exceeded`) the client can switch on. Messages for humans are the client's job.

## Contract

- The request/response schema lives in one place (`server/<aggregate>/schema.ts`) and the client imports its types. Never re-declare them by hand on the frontend.
- Changes are additive: new optional fields, new endpoints. Renaming, removing or retyping a field is a breaking change, so ask first and version it.
- Lists are paginated (`limit` with a server-side maximum + cursor or offset) and have a stable sort.
- Mutations that a retry could repeat (payments, sends, creates from a form) accept an idempotency key or are naturally idempotent (`PUT`, upsert).
- Rate-limit or quota checks run before any expensive work, and their 429 carries `retry-after` when known.

## Tests per endpoint

200 with the response shape · 400 on a malformed body · 401 without a session · 404 on another user's resource and on a malformed id · 403 for a wrong role (where roles exist). These run against the real DB engine (`data-access.md`), with only the session mocked.
