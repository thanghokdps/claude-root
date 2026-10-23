---
paths:
  - "**/*.{ts,tsx,mts}"
---

# Agent identity and tools

## Identity is trusted context, never a model argument

- Who the caller is comes from the verified request (token → server-side claims), injected by the server into the run. A tool reads it from that trusted context.
- A tool schema never has `userId`, `actingAs`, `tenantId`, `role` or any field that selects whose data or whose authority — that is an authorisation hole the model can be talked into filling.
- Targets the user names ("update Alex's leave") are resolved server-side and checked against the caller's permission on that specific resource.
- The trusted channel is the framework's run context: LangGraph/LangChain `contextSchema` → `runtime.context` (older: `config.configurable`), Mastra `requestContext`. The server fills it after verifying the token.
- Strip client-supplied identity keys from the run input, context and forwarded headers before injecting verified ones; `x-*` headers forwarded by an adapter are client-controlled. Keep access tokens out of context, `configurable` and state (they reach checkpoints and traces); use request scope (`AsyncLocalStorage`) instead.
- Shared context from the frontend (`useAgentContext`) is untrusted display context: fine for greetings and phrasing, never for authorisation.
- Missing or partial claims → refuse (fail closed), except an explicit dev-only fallback that cannot ship.

## Where a tool lives — agent or frontend

| The tool… | Define it | Skill |
|---|---|---|
| reads or writes server data, needs the caller's identity, a secret or an audit entry | agent tool (backend) | `/agent-tool`; writes add `/agent-hitl` |
| only changes the browser: navigate, open a panel, fill a form, read the selection, highlight | frontend tool, `useFrontendTool` | `/agent-frontend` |
| is a backend tool whose call or result the user should see | backend tool + `useRenderTool` card | `/agent-tool` then `/agent-frontend` |
| asks the user a question mid-turn (choose, clarify) | `useHumanInTheLoop` | `/agent-frontend` |
| needs both (fetch data, then show it in a panel) | two tools: backend read + frontend display; never one browser tool calling the API with the user's token | both |

- A frontend tool never writes server data and never decides authorisation: anything it can do, the user could do by clicking.
- Register a frontend tool only for the agent that may call it, and name it in that agent's prompt like any other tool.
- Tool name constants are shared (`shared/` package or module) so the backend registry, prompts and frontend renderers cannot drift.

## Tools

- Name and description live in constants; the description says when to use the tool and what it cannot do, in short bullets.
- Read tools: may retry on 429/502/503/504 and network errors, with backoff, honouring the abort signal.
- Mutation tools: never retried; gated by HITL (`interrupt()`); the only write before the decision is the pending-action record; the upstream write happens after confirm.
- Wrapper order: audit outside retry; every wrapper rethrows `GraphInterrupt`.
- Errors the user must see (forbidden, not found, ambiguous) become a short, deterministic answer — not a raw upstream error, and not something the model can paraphrase into a false success. Shape A: stock `toolErrorMiddleware({ onError })` maps them to an error `ToolMessage` and never swallows `GraphInterrupt`.
- A tool reporting a change that did not happen is a defect: confirm the outcome from the upstream response, not from the request.
- Every tool ships with its test: schema rejects identity fields, happy path, upstream error path; mutation tests assert no write before confirm.
