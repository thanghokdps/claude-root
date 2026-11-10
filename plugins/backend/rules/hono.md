---
paths:
  - "**/routes/**/*.ts"
  - "**/*.routes.ts"
  - "**/modules/**/routes.ts"
---

# Hono rules

Adds only what is Hono-specific. The handler order, error shape and owner scoping are in core's `api-contract.md`, `data-access.md` and `app-structure.md`; the runtime is in `cloudflare-workers.md`. Claims cite hono.dev (read 2026-11-10).

## Layout: one sub-app per aggregate

- Each aggregate exports its own `new Hono<AppEnv>()` from `src/modules/<aggregate>/routes.ts`, and the entry mounts it with `app.route('/channels', channels)` ([best practices](https://hono.dev/docs/guides/best-practices): "Building a larger application"). A route file holds routes only. The service and repository sit beside it (`service.ts`, `repository.ts`).
- Write the handler inline after the path, not as a Rails-style controller function: a separate `(c: Context) => …` loses path-param inference ([best practices](https://hono.dev/docs/guides/best-practices)). A handler stack reused across routes is built with `createFactory().createHandlers()` ([factory helper](https://hono.dev/docs/helpers/factory)).
- One `AppEnv = { Bindings: Env; Variables: { user: SessionUser } }`, generic on every `new Hono<AppEnv>()` and every `createMiddleware<AppEnv>()`. That way `c.env.DB` and `c.var.user` are typed everywhere ([context](https://hono.dev/docs/api/context)). Never read `env` from a module-level global.

## Request order: session → validate → service → DTO

- The session middleware runs before any validator, sets `c.set('user', …)`, and answers 401 itself, so unauthenticated input is never parsed. Mount it once on the API sub-app with `app.use('/api/*', session)`, never per route.
- Validate body, query and params with `zValidator(target, schema, hook)` from `@hono/zod-validator`, using the shared zod schemas ([validation](https://hono.dev/docs/guides/validation)). The `hook` maps a failure to the app's `{ error: 'invalid_input' }` 400, never zod's raw issue dump. Read the parsed value with `c.req.valid('json')`; never read `c.req.json()` again.
- `json` and `form` validators need a matching `Content-Type`. Without it the body is not parsed and the value is `{}` ([validation](https://hono.dev/docs/guides/validation)). Tests always send the header.
- The handler calls one service method with `(c.var.user.id, input)` and returns `c.json(dto, status)`. No SQL, no `c.env.DB` call and no business rule in a handler.

## Errors: one handler

- One `app.onError` maps every thrown error to `{ error: <code> }` with the status from `api-contract.md`. Services throw the app's `AppError(code, status)`, and `HTTPException` is mapped the same way ([HTTPException](https://hono.dev/docs/api/exception)). Unknown errors return 500 with no message or stack.
- A throw from a handler or middleware is caught and passed to `onError`, and `next()` never throws ([middleware](https://hono.dev/docs/guides/middleware)). So no `try/catch` in handlers builds an error response.

## Tests

- Route tests call `app.request(path, init)` and assert status and body ([testing](https://hono.dev/docs/guides/testing)). On Workers they run in `@cloudflare/vitest-plugin`, as Hono's testing guide recommends, so bindings are real.
- Every route gets the 200 · 400 · 401 · 404-for-another-user's-resource matrix from `/api-endpoint`.
