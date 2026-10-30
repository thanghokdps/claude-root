---
model: opus
effort: high
name: api-client
description: Builds a typed client for a third-party API the backend calls, from its OpenAPI spec or docs, with credentials from env or the request, timeouts, retries for idempotent reads only, error mapping, pagination, webhooks, and mocks so tests run without the network. Use when the backend must call an external service (payments, email, CRM, any REST API) or the user hands over an API spec, Postman collection or curl commands to integrate. The frontend calling its own backend is ui-feature's job.
when_to_use: integrate API, "tích hợp API", "gọi API bên thứ ba", call external API from backend, third-party service, REST client, OpenAPI client, swagger, postman, API timeout, retry, webhook client, payment provider, email provider
---

# api-client

**Invoke:** `/api-client <which API, from where>`

Rules: `api-contract.md`, `app-structure.md` and `security.md` from core. Turning an API into tools for an AI agent → `/agent-tool` (ai, if installed), which builds on the same client layer. The frontend calling the app's own backend is `/ui-feature` (frontend, if installed), not this skill.

---

## Step 1 — What exists

The client lives in `server/<system>/{client,errors,mappers}.ts`. Look for an existing client for that system, its env schema entries, and the repo's `stubFetch`/MSW helpers. A second client for the same API is a defect.

**Done when:** the files to change and the helpers to reuse are named with paths.

## Step 2 — Build the client

1. **One source of truth.** Take an OpenAPI spec as given, or write the subset you need from docs, Postman or curl into `docs/api/<system>.openapi.yaml`, and confirm it with the user. Never invent fields or endpoints. A real key in a pasted example: tell the user to rotate it and never echo it.
2. **Types and client.** Generate types (`openapi-typescript <spec> -o server/<system>/schema.d.ts`) with an `api:types` script, and create the client with `openapi-fetch` `createClient<paths>({ baseUrl })`, or hand-write a small typed client when there is no spec. Base URL, key and timeout go in the env schema.
3. **Credentials.** A server key comes from env. A per-user token comes from the request scope per call, never a module-level variable. Record which mode the system uses.
4. **Resilience.** A timeout on every call, plus the request's abort signal. Retry with backoff only on idempotent reads (GET, or with an idempotency key) for 429/5xx and network errors. Never retry a payment or a send without a key. Follow the API's pagination, with a cap.
5. **Errors and mapping.** `errors.ts` maps upstream status and error bodies to the app's own error codes. `mappers.ts` turns upstream payloads into the app's types, so nothing upstream-shaped leaks into routes or UI.
6. **Mocks.** MSW handlers from the spec's examples (`fromOpenApi` from `@msw/source/open-api`) or the repo's `stubFetch` helper. Tests cover success, each mapped error, a timeout, and a retry that gives up.
7. **Webhooks** from that system, if any: verify the signature with the raw body, dedupe by event id, and respond fast while queueing the work. This is a hard gate, so treat it as high-risk.

Check every new package (maintainer, downloads, what it does) before adding it, and pin it exactly.

**Done when:** the Step 2 tests pass with no network, plus typecheck and lint.

## Step 3 — Prove it

Make one real call against the dev or sandbox API, or the running backend, through the new client, and show the mapped result and one mapped error. Never call a production API with real side effects to test.

**Done when:** the smoke call output is pasted, with credentials redacted.

---

Hand-offs: the endpoint on our side → `/api-endpoint` · the screen using it → `/ui-feature` (frontend, if installed) · webhooks or payment providers → high-risk lane (`/coordinator`) · done → `/verify-done` → `/review-checklist`.
