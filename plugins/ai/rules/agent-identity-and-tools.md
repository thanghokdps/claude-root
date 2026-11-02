---
paths:
  - "**/*.{ts,tsx,mts}"
---

# Agent identity and tools

## Identity is trusted context, never a model argument

- Who the caller is comes from the verified request (token → server-side claims), injected by the server into the run. A tool reads it from that trusted context.
- A tool schema never has `userId`, `actingAs`, `tenantId`, `role` or any field that selects whose data or whose authority — that is an authorisation hole the model can be talked into filling.
- Targets the user names ("update Alex's leave") are resolved server-side and checked against the caller's permission on that specific resource. A write target's id must match a row a trusted read tool returned in this thread; an id from model text or client-sent history is refused.
- The trusted channel is the framework's run context: LangGraph/LangChain `contextSchema` → `runtime.context` (older: `config.configurable`), Mastra `requestContext`. The server fills it after verifying the token. A `createAgent` graph served by the LangGraph server gets an empty `context` and uses `configurable` instead (`langgraph.md` § Run context).
- Strip client-supplied identity keys from the run input, context and forwarded headers before injecting verified ones; `x-*` headers forwarded by an adapter are client-controlled. Keep access tokens out of context, `configurable` and state (they reach checkpoints and traces); use request scope (`AsyncLocalStorage`) instead.
- Shared context from the frontend (`useAgentContext`) is untrusted display context: fine for greetings and phrasing, never for authorisation.
- Missing or partial claims → refuse (fail closed), except an explicit dev-only fallback that cannot ship.

## Where a tool lives — agent or frontend

| The tool… | Define it | Skill |
|---|---|---|
| reads or writes server data, needs the caller's identity, a secret or an audit entry | agent tool (backend) | `/agent-tool`; writes add `/agent-hitl` |
| only changes the browser: navigate, open a panel, fill a form, read the selection, highlight | frontend tool, `useFrontendTool` | `/agent-frontend` |
| reads server data and shows the result **inside the chat** (a card under the answer) | backend tool + `useRenderTool` card; the card only draws the result, it is not a tool | `/agent-tool` then `/agent-frontend` |
| asks the user a question mid-turn (choose, clarify) | `useHumanInTheLoop` | `/agent-frontend` |
| proposes a change the user applies (a new title, a draft): the agent never writes | read-only backend tool returning the proposal + `useRenderTool` card whose Confirm calls the app's existing route, as the user, exactly like the UI button | `/agent-tool` then `/agent-frontend` |
| reads server data, then changes the page **outside the chat** (opens a side panel, highlights a row) | two tools the model calls in a row: a backend read, then a frontend tool that receives the data; never one browser tool calling the API with the user's token | both |

- The two read rows differ only in where the result goes: in the chat → one backend tool and a card; on the page → add a frontend tool, because only the browser can open a panel.
- A frontend tool never writes server data and never decides authorisation: anything it can do, the user could do by clicking.
- Agent writes vs user writes: when the agent's tool performs the write, gate it with `/agent-hitl` (backend interrupt). When the agent only proposes and the user's click sends the write through a route the UI already uses (same auth, same ownership check), that is a user write: no interrupt, no pending-action record. The tool stays read-only; it never calls the write route itself.
- Register a frontend tool only for the agent that may call it, and name it in that agent's prompt like any other tool.
- Frontend tools arrive with the run input (`RunAgentInput.tools`); unfiltered, they reach every agent and subagent of the graph. Filter them server-side per agent against that agent's bound tool set; a supervisor or subagent never sees a browser tool it was not given.
- Tool name constants are shared (`shared/` package or module) so the backend registry, prompts and frontend renderers cannot drift.

## Tools

- Name and description live in constants; the description says when to use the tool and what it cannot do, in short bullets.
- Every upstream call has a deadline (`AbortSignal.timeout` or the client's timeout); no call waits forever.
- Read tools: may retry on 429/502/503/504 and network errors, with backoff, honouring the abort signal.
- Mutation tools: never retried; gated by HITL (`interrupt()`); the only write before the decision is the pending-action record; the upstream write happens after confirm.
- Wrapper order: audit outside retry; every wrapper rethrows `GraphInterrupt`.
- Errors the user must see (forbidden, not found, ambiguous) become a short, deterministic answer — not a raw upstream error, and not something the model can paraphrase into a false success. Shape A: stock `toolErrorMiddleware({ onError })` maps them to an error `ToolMessage` and never swallows `GraphInterrupt`.
- A tool reporting a change that did not happen is a defect: confirm the outcome from the upstream response, not from the request.
- Every tool ships with its test: schema rejects identity fields, happy path, upstream error path; mutation tests assert no write before confirm.
