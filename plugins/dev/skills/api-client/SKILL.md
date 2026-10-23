---
model: opus
effort: high
name: api-client
description: Integrates with an API. On the frontend that means typed fetchers calling the app's own backend, with errors mapped to UI states. On the backend it means a typed client for a third-party API from its OpenAPI spec or docs, with credentials from env or the request, timeouts, retries for idempotent reads only, error mapping, pagination, and mocks so tests run without the network. Use when the frontend must call a backend endpoint, the backend must call an external service (payments, email, CRM, any REST API), or the user hands over an API spec, Postman collection or curl commands to integrate.
when_to_use: integrate API, "tích hợp API", "gọi API bên thứ ba", call external API from backend, third-party service, REST client, OpenAPI client, swagger, postman, fetch wrapper, frontend calls backend, typed fetcher, API timeout, retry, webhook client, "frontend gọi API backend"
---

# api-client

**Invoke:** `/api-client <which API, from where>`

Rules: `api-contract.md`, `app-structure.md` and `security.md` from core. Turning an API into tools for an AI agent → `/agent-tool` (agent, if installed), which builds on the same client layer.

---

## Step 1 — Which direction, and what exists

| Direction | Where it lives | Look for |
|-----------|----------------|----------|
| Frontend → own backend | `features/<f>/api.ts` | a shared `fetchJson` helper, the backend's exported schema types, TanStack Query/SWR |
| Backend → external API | `server/<system>/{client,errors,mappers}.ts` | an existing client per system, env schema entries, `stubFetch`/MSW helpers |

Reuse the shared fetch helper and the existing client for that system. A second client for the same API is a defect.

**Done when:** the direction, the files to change and the helpers to reuse are named with paths.

## Step 2 — Frontend → own backend

- One typed function per endpoint in the feature's `api.ts`, through the shared helper. Request and response types are **imported** from the backend schema (`server/<aggregate>/schema.ts` or a shared package), never re-declared.
- The helper turns non-2xx into a typed error carrying the backend's `error` code. The UI switches on the code (`not_found`, `quota_exceeded`) and never parses messages.
- Use the repo's caching library (keys, invalidation after a write). Without one, refetch after a successful write rather than patching scattered state.
- Tests mock at the fetch boundary and cover the success shape, an error code, and a network failure.

## Step 3 — Backend → external API

1. **One source of truth.** Take an OpenAPI spec as given, or write the subset you need from docs, Postman or curl into `docs/api/<system>.openapi.yaml`, and confirm it with the user. Never invent fields or endpoints. A real key in a pasted example: tell the user to rotate it and never echo it.
2. **Types and client.** Generate types (`openapi-typescript <spec> -o server/<system>/schema.d.ts`) with an `api:types` script, and create the client with `openapi-fetch` `createClient<paths>({ baseUrl })`, or hand-write a small typed client when there is no spec. Base URL, key and timeout go in the env schema.
3. **Credentials.** A server key comes from env. A per-user token comes from the request scope per call, never a module-level variable. Record which mode the system uses.
4. **Resilience.** A timeout on every call, plus the request's abort signal. Retry with backoff only on idempotent reads (GET, or with an idempotency key) for 429/5xx and network errors. Never retry a payment or a send without a key. Follow the API's pagination, with a cap.
5. **Errors and mapping.** `errors.ts` maps upstream status and error bodies to the app's own error codes. `mappers.ts` turns upstream payloads into the app's types, so nothing upstream-shaped leaks into routes or UI.
6. **Mocks.** MSW handlers from the spec's examples (`fromOpenApi` from `@msw/source/open-api`) or the repo's `stubFetch` helper. Tests cover success, each mapped error, a timeout, and a retry that gives up.
7. **Webhooks** from that system, if any: verify the signature with the raw body, dedupe by event id, and respond fast while queueing the work. This is a hard gate, so treat it as high-risk.

Check every new package (maintainer, downloads, what it does) before adding it, and pin it exactly.

**Done when:** the Step 2 or Step 3 tests pass with no network, plus typecheck and lint.

## Step 4 — Prove it

Make one real call against the dev or sandbox API, or the running backend, through the new client, and show the mapped result and one mapped error. Never call a production API with real side effects to test.

**Done when:** the smoke call output is pasted, with credentials redacted.

---

Hand-offs: the endpoint on our side → `/api-endpoint` · the screen using it → `/ui-feature` · webhooks or payment providers → high-risk lane (`/coordinator`) · done → `/verify-done` → `/review-checklist`.
