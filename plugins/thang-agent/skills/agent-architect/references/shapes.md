# Agent shapes — detect, then choose

Every `agent-*` skill starts here. A recipe applied to the wrong shape edits the wrong layer.

## Detect (facts — grep, never ask)

```bash
rg -l "createAgent\(" --type ts            # A: prebuilt agent + middleware
rg -l "new StateGraph\(" --type ts         # custom graph (B, or a hybrid supervisor)
rg -l "CopilotRuntime" --type ts           # A transport: CopilotKit runtime (Node)
rg -l "extends AbstractAgent" --type ts    # B transport: own AG-UI emitter
rg -l "createEmbedServer|langgraph-api" --type ts   # LangGraph platform app served in-process
cat langgraph.json 2>/dev/null; ls wrangler.* 2>/dev/null   # graph registry · Workers host
```

Record the result as one line before any edit: `Shape: A | B | hybrid · host: node | workers · transport: runtime | own-emitter`.
Then read `docs/adr/*` if present: the recorded architecture card binds every `agent-*` change. A change that needs a new agent, shape, write path, system or client is an architecture change — stop and ask (`/agent-feature` Step 2), never widen it inside the change.
Mixed signals (both shapes in one app) → name the app/package each belongs to; never average them.

## Shape A — prebuilt agent (greenfield default)

- `createAgent({ model, tools, middleware })`; behaviour lives in middleware hooks (`beforeAgent`, `wrapModelCall`, `wrapToolCall`, `afterAgent`).
- Transport: `CopilotRuntime` (Node) with a `LangGraphAgent` adapter; client uses CopilotKit v2 hooks.
- Tools may be schema-only, executed inside a `wrapToolCall` middleware that injects trusted context.
- Middleware order is a contract: context/memory → domain tools → shared context → summarisation → CopilotKit → fallback last.

## Shape B — custom graph + own emitter (Workers-native branch)

- `new StateGraph(State)` with explicit nodes (e.g. agent → tools → finalize) and edges.
- Transport: an `AbstractAgent` subclass translating `streamEvents` v2 into AG-UI SSE; no CopilotKit runtime (it needs Node).
- Tools are real handlers reading per-request context from `config.configurable`.
- Choose B on purpose: edge/Workers host, or a transport/state contract the runtime cannot express.

## Hybrid — supervisor graph over prebuilt agents

- A `StateGraph` supervisor (prepare → router → subagent nodes → decline/handoff) whose nodes are `createAgent(...)` graphs.
- The common best shape once there is more than one domain.

## createAgent or StateGraph — the decision rule

Use `createAgent` when the work is one LLM ⇄ tools loop whose extra behaviour fits a middleware hook.

Use a `StateGraph` (alone or as a supervisor) when any of these is true:

- a step the model must not skip or reorder (validate → then write; load context → then answer)
- routing to specialised agents with different tools/prompts
- parallel fan-out over independent work, or an evaluator → retry loop
- non-LLM steps (prepare, persist, notify) or per-node streaming control
- one agent would carry more than ~10–15 tools (route, or `llmToolSelectorMiddleware`)

A hand-built `agent → tools → agent` loop with nothing else re-implements `createAgent`: list it as an audit candidate.
