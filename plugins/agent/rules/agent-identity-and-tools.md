---
paths:
  - "**/*.{ts,tsx,mts}"
---

# Agent identity and tools

## Identity is trusted context, never a model argument

- Who the caller is comes from the verified request (token → server-side claims), injected by the server into the run. A tool reads it from that trusted context.
- A tool schema never has `userId`, `actingAs`, `tenantId`, `role` or any field that selects whose data or whose authority — that is an authorisation hole the model can be talked into filling.
- Targets the user names ("update Alex's leave") are resolved server-side and checked against the caller's permission on that specific resource.
- Strip client-supplied identity keys from the run config before injecting verified ones. Keep access tokens out of `configurable`/state (both reach checkpoints and traces); use request scope (`AsyncLocalStorage`) instead.
- Shared context from the frontend (`useAgentContext`) is untrusted display context: fine for greetings and phrasing, never for authorisation.
- Missing or partial claims → refuse (fail closed), except an explicit dev-only fallback that cannot ship.

## Tools

- Name and description live in constants; the description says when to use the tool and what it cannot do, in short bullets.
- Read tools: may retry on 429/502/503/504 and network errors, with backoff, honouring the abort signal.
- Mutation tools: never retried; gated by HITL (`interrupt()`); the only write before the decision is the pending-action record; the upstream write happens after confirm.
- Wrapper order: audit outside retry; every wrapper rethrows `GraphInterrupt`.
- Errors the user must see (forbidden, not found, ambiguous) become a short, deterministic answer — not a raw upstream error, and not something the model can paraphrase into a false success.
- A tool reporting a change that did not happen is a defect: confirm the outcome from the upstream response, not from the request.
- Every tool ships with its test: schema rejects identity fields, happy path, upstream error path; mutation tests assert no write before confirm.
