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

- Declare `contextSchema` (zod) on `createAgent` / `StateGraph` and pass `{ context }` at invoke. Tools and `createAgent` middleware read `runtime.context` (`ToolRuntime`; middleware gets `(state, runtime)`); a `StateGraph` node gets `(state, config)` and reads `config.context`. `config.configurable` is a supported configuration channel, not deprecated — the exception below says when it is the trusted one.
- Once a graph publishes a context schema and the run's `configurable` holds at least one of its keys, `@ag-ui/langgraph` moves only those keys into `context` and **drops the rest**, silently when served by the LangGraph server (`@ag-ui/langgraph@0.0.45 dist/index.mjs:2`: `mergeConfigs` filters `configurable` to the config + context schema keys, and the server serves the same schema for both, so `shapePayloadConfig`'s console warning is never reached; observed on `langgraphjs dev` 1.5.7: an extra `configurable` key vanished, no warning). The schema keys come from `getSchemas()` at `:6`, `getSchemaKeys`. Put every trusted key in the schema; a test asserts a tool sees the caller's id through the adapter.
- The adapter copies the client's `x-*` request headers into `configurable.copilotkit_forwarded_headers`. They are client-controlled: never read identity from them unless the server replaced them after verifying the token.
- **Exception, served by the LangGraph server:** `@langchain/langgraph-api@1.5.7` (the version `@langchain/langgraph-cli@1.5.7`, which ships `langgraphjs`, pins) publishes no context schema for a graph built on a `StateSchema` (`createAgent`, or any graph with `CopilotKitStateSchema`: `dist/graph/parser/index.mjs:90-91` sets `config = undefined`, and `dist/api/assistants.mjs:141-143` serves `context_schema: schema.config`) and runs it with an empty `context` (`dist/storage/ops.mjs:1035-1037` fills a run's `context` only from the assistant's and the request's), so a `contextSchema` on it rejects every run (`userId: Required`). There the trusted channel is `configurable`: the CopilotKit runtime route sets `LangGraphAgent({ assistantConfig: { configurable: { userId } } })` (the `@ag-ui/langgraph` class of § Transport; `assistantConfig?: Config` at 0.0.45 `dist/index.d.ts:143`) and the graph reads it with a fail-closed reader. In a `StateGraph` node the reader is `(state, config)` → `config.context` with `contextSchema`, else `config.configurable` (both on `Runtime` / `LangGraphRunnableConfig`, @langchain/langgraph 1.6.0 `dist/pregel/runnable_types.d.ts:36-39`); `runtime.context` is the `createAgent` middleware argument, not a node's. Check `GET /assistants/<id>/schemas` first; a non-empty `context_schema` means `contextSchema` works.
- `@ag-ui/langgraph@0.0.45` reduces `[assistantConfig, forwardedProps.config]` in that order and a later `configurable` replaces the earlier one whole (`dist/index.mjs:2`, `mergeConfigs`), so a client can overwrite a server-set key. The CopilotKit route drops `forwardedProps.config` in `beforeRequestMiddleware` before any run, and returns the new request rebuilt from its parts — `new Request(request.url, { method, headers, body, signal })`, as the runtime's own `createJsonRequest` does (@copilotkit/runtime 1.83.0 `dist/v2/runtime/endpoints/single-route-helpers.mjs:71`). `new Request(request, …)` throws `Cannot read private member #state` on the request a Next.js route passes in, so every forged request gets a 500; a test passes a `Proxy` around a `Request` to cover it.
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
- `langgraph dev` serves on `:2024` and opens LangGraph Studio in the browser (CLI: `--no-browser` skips it, `--studio-url` defaults to `https://smith.langchain.com`); the graph renders there and every run appears in it. The closing message shows that URL as the CLI printed it (it carries `baseUrl=` for the local server), never a generic domain.

## Models

- `temperature: 0` for anything that routes or produces structured output.
- Structured output that fails to parse, and has no free-text fallback that yields the field, becomes an explicit `needs_review` value the caller handles, never the schema's default or the middle option: a guessed default is read later as a decision the model made.
- Check model-specific options against the bound tools (some models reject reasoning-effort with tools); verify on the installed model, not from memory.

## Fixed workflows

- A fixed order of steps (validate → approve → write) is a `StateGraph` with fixed edges and a typed state, not a prompt instruction; conditional edges only where a step's output decides the branch.
- Every conditional edge driven by one router maps every target that router can return, from one shared constant, including its fall-through; a test calls the router with an unexpected value and asserts the target is in the map.
- Compile it once at module level with the checkpointer, and expose it to the agent as one tool or a subgraph node.
- A step that waits for a human uses `interrupt()` per § Interrupts; code before it runs again on resume, so make it idempotent.

## Transport (CopilotKit runtime)

- The runtime is a route on the LangGraph server itself, never a server written for the web app. `langgraph.json` registers it with `"http": { "app": "./src/<langchain|langgraph>/copilotkit.ts:app" }`. Custom routes must be a Hono app, work under `langgraph dev` and `langgraph up`, and take priority over the built-in endpoints (docs.langchain.com/langsmith/custom-routes), so Hono lives only in the agent folder.
- `copilotkit.ts` exports a Hono app mounting `createCopilotHonoHandler({ runtime, basePath: "/api/copilotkit" })` from `@copilotkit/runtime/v2/hono` (CopilotKit `examples/v2/runtime/hono`). The runtime holds `new LangGraphAgent({ deploymentUrl, graphId: AGENT_ID })` from **`@ag-ui/langgraph`** (0.0.45, `dist/index.d.ts:128` `LangGraphAgentConfig { deploymentUrl, graphId, assistantConfig?, … }`), passed to the v2 `CopilotRuntime({ agents })`, with `deploymentUrl` this same server (`LANGGRAPH_DEPLOYMENT_URL`, `http://localhost:2024` under `langgraph dev`). `@copilotkit/runtime/langgraph` (`LangGraphAgent`, `LangGraphHttpAgent`) is the v1 entry, `@deprecated Since 1.68.2` (@copilotkit/runtime 1.83.0, `dist/langgraph.d.mts:6`); CopilotKit's own examples still import it, so never copy that line from them — `@typescript-eslint/no-deprecated` fails it.
- CORS on the route is limited to the web origin, never `*`. Identity follows § Run context: the route verifies the caller, sets `assistantConfig.configurable`, and drops `forwardedProps.config`.
- The Vite client calls `${VITE_LANGGRAPH_BASE_URL}/api/copilotkit`. Only when the user names Next.js does the runtime move to a Next.js route beside an `agent/` package (R4).

## Streaming

- `streamEvents(input, { version: "v2" })` — always v2.

## Interrupts

- `interrupt()` needs a checkpointer and a stable `thread_id`; resume with `new Command({ resume })` on the same thread.
- Put `reason` (`tool_call`), `toolCallId`, `message` and `expiresAt` in the interrupt value: `@ag-ui/langgraph` maps them onto the standard AG-UI interrupt (its `id` is LangGraph's interrupt id) and the rest of the value lands in `metadata.langgraph.raw` (`agui-transport.md` § Interrupts).
- Code above `interrupt()` re-runs on resume: make it idempotent. The only write allowed above it is the pending-action record (see `agent-identity-and-tools.md`).
- Code below `interrupt()` runs once, after the decision — that is where the real write happens.
- Never retry a node or tool that can raise `GraphInterrupt`; rethrow it from every wrapper.
