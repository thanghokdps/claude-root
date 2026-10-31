---
paths:
  - "**/*.{ts,tsx,mts}"
  - "**/langgraph.json"
---

# LangGraph rules (TypeScript)

## State

- Reducer channels (`messages`) **append**: a node returns only the delta, never the concatenated history.
- A node returns `Partial<State>` with only the fields it changes; clear a field explicitly (`field: null`), never by omission.
- Keep state small and serialisable — it is checkpointed every turn. Large or rotating values (tokens, clients, adapters) go in the run context or request scope, never in state.
- Values written once at graph entry (identity, model choice) are never mutated by later nodes.

```typescript
return { messages: [aiResponse] };                    // delta — correct
return { messages: [...state.messages, aiResponse] }; // duplicates history
```

## Run context (identity, per-run dependencies)

- Declare `contextSchema` (zod) on `createAgent` / `StateGraph` and pass `{ context }` at invoke. Tools read `runtime.context` (`ToolRuntime`), nodes and middleware read `runtime.context`. `config.configurable` is the older path.
- Once a graph declares `contextSchema`, `@ag-ui/langgraph` moves only the schema's keys from `configurable` into `context` and **drops the rest** with a console warning. Put every trusted key in the schema; a test asserts a tool sees the caller's id through the adapter.
- The adapter copies the client's `x-*` request headers into `configurable.copilotkit_forwarded_headers`. They are client-controlled: never read identity from them unless the server replaced them after verifying the token.
- **Exception, served by the LangGraph server:** `@langchain/langgraph-api` (checked 1.5.6) publishes no context schema for a graph built on a `StateSchema` (`createAgent`, or any graph with `CopilotKitStateSchema`) and runs it with an empty `context`, so a `contextSchema` on it rejects every run (`userId: Required`). There the trusted channel is `configurable`: the web server sets `LangGraphAgent({ assistantConfig: { configurable: { userId } } })` and the graph reads it with a fail-closed reader. Check `GET /assistants/<id>/schemas` first; a non-empty `context_schema` means `contextSchema` works.
- `@ag-ui/langgraph` (checked 0.0.44) merges the browser's `forwardedProps.config` **over** `assistantConfig`, so a client can overwrite a server-set key. The CopilotKit route drops `forwardedProps.config` in `beforeRequestMiddleware` before any run.
- Per-turn values (trace callbacks, the caller) come through a graph factory in `langgraph.json` (`export const graph = (config, runtime) => …`; `runtime.executionRuntime` is null on schema reads). Return `agent.graph.withConfig({ callbacks })` on the agent compiled once; `ReactAgent.withConfig()` recompiles it.

## Long-term memory

- Conversation memory is the checkpointer (per `thread_id`); memory across threads goes in a LangGraph Store, never in graph state or the system prompt.
- Namespace every Store key by the user id from trusted context (`["memories", userId, kind]`), never by an id the model or client supplies.
- Writes to memory are tool calls the user can see and delete; recalled memory is untrusted input to the prompt, like a tool result.

## Graph lifecycle

- Compile once at module level with its dependencies; invoke many times. Never compile or build a checkpointer per request.
- Pass per-run limits at invoke time: `recursionLimit`, timeout, abort `signal`.
- `GraphRecursionError` and timeouts end as a readable assistant turn, never a 500.
- An agent that loops model → tools counts its tool rounds; at the cap it gets one last turn told to answer with what it has, and that turn ends the loop whatever it returns, so a model that keeps calling tools ends with an answer instead of the recursion limit.
- Nodes that route, prepare or summarise must not stream into the chat: tag them `nostream` / disable message emission.

## Models

- `temperature: 0` for anything that routes or produces structured output.
- Structured output that fails to parse, and has no free-text fallback that yields the field, becomes an explicit `needs_review` value the caller handles, never the schema's default or the middle option: a guessed default is read later as a decision the model made.
- Check model-specific options against the bound tools (some models reject reasoning-effort with tools); verify on the installed model, not from memory.

## Fixed workflows

- A fixed order of steps (validate → approve → write) is a `StateGraph` with fixed edges and a typed state, not a prompt instruction; conditional edges only where a step's output decides the branch.
- Every conditional edge driven by one router maps every target that router can return, from one shared constant, including its fall-through; a test calls the router with an unexpected value and asserts the target is in the map.
- Compile it once at module level with the checkpointer, and expose it to the agent as one tool or a subgraph node.
- A step that waits for a human uses `interrupt()` per § Interrupts; code before it runs again on resume, so make it idempotent.

## Streaming

- `streamEvents(input, { version: "v2" })` — always v2.

## Interrupts

- `interrupt()` needs a checkpointer and a stable `thread_id`; resume with `new Command({ resume })` on the same thread.
- Put `reason` (`tool_call`), `toolCallId`, `message` and `expiresAt` in the interrupt value: `@ag-ui/langgraph` maps them onto the standard AG-UI interrupt (its `id` is LangGraph's interrupt id) and the rest of the value lands in `metadata.langgraph.raw` (`agui-transport.md` § Interrupts).
- Code above `interrupt()` re-runs on resume: make it idempotent. The only write allowed above it is the pending-action record (see `agent-identity-and-tools.md`).
- Code below `interrupt()` runs once, after the decision — that is where the real write happens.
- Never retry a node or tool that can raise `GraphInterrupt`; rethrow it from every wrapper.
