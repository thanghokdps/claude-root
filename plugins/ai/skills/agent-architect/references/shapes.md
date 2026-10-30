# Agent shapes — detect, then choose

Every `agent-*` skill starts here. A recipe applied to the wrong shape edits the wrong layer.

## Detect (facts — grep, never ask)

```bash
rg -l "createAgent\(" --type ts            # A: prebuilt agent + middleware
rg -l "new StateGraph\(" --type ts         # custom graph (B, or a hybrid supervisor)
rg -l "CopilotRuntime" --type ts           # A transport: CopilotKit runtime (Node)
rg -l "extends AbstractAgent" --type ts    # B transport: own AG-UI emitter
rg -l "createEmbedServer|langgraph-api" --type ts   # LangGraph platform app served in-process
rg -l "new Mastra\(|from ['\"]@mastra/core" --type ts   # M: Mastra registry and agents
rg -l "@ag-ui/mastra" --type ts            # M transport: AG-UI adapter (in-process or registerCopilotKit)
cat langgraph.json 2>/dev/null; ls wrangler.* 2>/dev/null   # graph registry · Workers host
```

Record the result as one line before any edit: `Shape: A | B | hybrid | M · host: node | workers · transport: runtime | own-emitter | mastra-server`.
Then read `docs/adr/*` if present: the recorded architecture card binds every `agent-*` change. A change that needs a new agent, shape, write path, system or client is an architecture change — stop and ask (`/agent-feature` Step 2), never widen it inside the change.
Mixed signals (both shapes in one app) → name the app/package each belongs to; never average them.

**Speak only the chosen framework.** Once the shape is recorded (or chosen in `/agent-architect` Q-F), every reply, question, option, plan, ADR, doc and code comment uses only that framework's names. On LangChain/LangGraph (A, B, hybrid) never mention Mastra; on Mastra (M) never mention LangChain or LangGraph. Read only that framework's rules file (`langgraph.md` or `mastra.md`). The other framework comes up only when the user asks about it, or in Q-F before a framework is chosen.

## Shape A — prebuilt agent (greenfield default)

- `createAgent({ model, tools, middleware })`; behaviour lives in middleware hooks (`beforeAgent`, `wrapModelCall`, `wrapToolCall`, `afterAgent`).
- Transport: `CopilotRuntime` (Node) with a `LangGraphAgent` adapter; client uses CopilotKit v2 hooks.
- Tools may be schema-only, executed inside a `wrapToolCall` middleware that injects trusted context. Trusted values travel in `contextSchema` → `runtime.context`.
- Middleware order is a contract: context/memory → domain tools → shared context → summarisation → CopilotKit → fallback last.

## Shape B — custom graph + own emitter (Workers-native branch)

- `new StateGraph(State)` with explicit nodes (e.g. agent → tools → finalize) and edges.
- Transport: an `AbstractAgent` subclass translating `streamEvents` v2 into AG-UI SSE; no CopilotKit runtime (it needs Node).
- Tools are real handlers reading per-request context from `runtime.context` (`contextSchema` on the graph; older: `config.configurable`).
- On AG-UI ≥ 1.0 the emitter owns what an adapter would: `protocolVersion` on `RUN_STARTED`, `REASONING_*` spans closed, extra data only in `metadata`, the standard interrupt outcome and `resume[]` handling (`${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`). Build its events with the `@ag-ui/core` types and validate them with `@ag-ui/core/schemas` in tests.
- Choose B on purpose: edge/Workers host, or a transport/state contract the runtime cannot express.

## Hybrid — supervisor graph over prebuilt agents

- A `StateGraph` supervisor (prepare → router → subagent nodes → decline/handoff) whose nodes are `createAgent(...)` graphs.
- The common best shape once there is more than one domain.

## Shape M — Mastra

- One registry: `export const mastra = new Mastra({ agents, tools, workflows, storage, logger, observability })` in `src/mastra/index.ts`. Every agent, workflow and tool is registered there, keyed by its id.
- Agents are `new Agent({ id, instructions, model, tools, memory })`. Tools are `createTool({ id, description, inputSchema, outputSchema, execute })`, and `execute(input, context)` reads trusted values from `context.requestContext`.
- Supervisor: an `Agent` with `agents: { … }`, where each subagent carries a `description` the supervisor routes by. `.network()` is deprecated, so do not start new work on it. A fixed sequence is a workflow (`createWorkflow` + `createStep`, `.then()`/`.branch()`/`.parallel()`), not a prompt.
- Writes: `requireApproval: true` on the tool, or `suspend()`/`resume` in the tool or a workflow step. Either needs `storage` configured.
- Transport: `@ag-ui/mastra`, either in-process (`MastraAgent.getLocalAgents({ mastra })` behind the CopilotKit route) or a Mastra server exposing `registerCopilotKit({ path, resourceId })` in `server.apiRoutes`.
- Rules: `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md`.

## Framework — the first decision (interview Q-F)

The stack the user names wins: "Mastra", "LangChain", "LangGraph" or "custom graph" in the request or the repo is a fact, not a question. Otherwise:

- **A** (LangChain `createAgent`) is the default: one LLM ⇄ tools loop, Node host, CopilotKit runtime.
- **M** (Mastra) when the team already runs Mastra, or wants workflows, memory, storage, evals and a dev studio from one framework.
- **B / hybrid** (custom LangGraph graph) when the decision rule below needs a `StateGraph`, the host is edge/Workers, or a contract the runtime cannot express.

Mixing frameworks in one agent is never a default. Two frameworks in one repo means two apps or packages, each with its own shape line.

## createAgent or StateGraph — the decision rule

Mastra equivalent: one `Agent` where this rule says `createAgent`, a workflow where it says a fixed sequence or non-LLM steps, and a supervisor `Agent` where it says routing.

Use `createAgent` when the work is one LLM ⇄ tools loop whose extra behaviour fits a middleware hook.

Use a `StateGraph` (alone or as a supervisor) when any of these is true:

- a step the model must not skip or reorder (validate → then write; load context → then answer)
- routing to specialised agents with different tools/prompts
- parallel fan-out over independent work, or an evaluator → retry loop
- non-LLM steps (prepare, persist, notify) or per-node streaming control
- one agent would carry more than ~10–15 tools (route, or `llmToolSelectorMiddleware`)

A hand-built `agent → tools → agent` loop with nothing else re-implements `createAgent`: list it as an audit candidate.
