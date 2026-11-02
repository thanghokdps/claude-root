# Stock map — L0 building blocks

Verified against vendor source on 2026-10-23 (langchain 1.5.19, @langchain/langgraph 1.5.2, @copilotkit/* 1.79.1, @ag-ui/core 1.0.3, @ag-ui/langgraph 0.0.45, @ag-ui/mastra 2.0.1). Docs for these packages disagree across versions: before relying on a row, confirm the export exists in the **installed** package (`node_modules/<pkg>/package.json` → `exports`, or grep its `.d.ts`).

## Backend

| Need | Stock (L0/L1) | Notes |
|------|---------------|-------|
| Agent loop | `createAgent` (`langchain`) | Usable as a node/subgraph inside a `StateGraph` |
| Retry tool calls | `toolRetryMiddleware({ tools, retryOn, maxRetries })` | Pass read tools only — mutations are never retried |
| Retry model calls | `modelRetryMiddleware` | |
| Provider fallback | `modelFallbackMiddleware(...models)` | Place last so a fallback retries the fully decorated request |
| Long threads | `summarizationMiddleware({ model, trigger, keep })` | Give the summary model message emission off, or the summary shows as a chat bubble |
| Tool errors → short answer | `toolErrorMiddleware({ onError, tools })` | Returns an error `ToolMessage`; LangGraph control flow (`GraphInterrupt`) always propagates |
| Prompt per run (static first, dynamic last) | `dynamicSystemPromptMiddleware((state, runtime) => …)` | Reads `runtime.context`; keep the static prefix byte-stable for caching |
| Prompt caching | `anthropicPromptCachingMiddleware`, `bedrockPromptCachingMiddleware` | OpenAI caches automatically; measure cached tokens in tracing |
| Moderation | `openAIModerationMiddleware` | Input/output guard; not an authorisation check |
| Multi-step plans | `todoListMiddleware` | Only when the agent really plans; adds tokens every call |
| Old tool output bloat | `contextEditingMiddleware` | Clears old tool results past a token trigger |
| Runaway loops / cost | `modelCallLimitMiddleware`, `toolCallLimitMiddleware` | Thread limits need a checkpointer |
| PII | `piiMiddleware({ strategy })`, `piiRedactionMiddleware` | Complements trace masking; not a substitute |
| Too many tools | `llmToolSelectorMiddleware({ maxTools, alwaysInclude })`, or `providerToolSearchMiddleware({ searchableTools })` (provider-side search, `defer_loading`; OpenAI/Anthropic models that support it) | Or route to sub-agents |
| Approval of tool calls | `humanInTheLoopMiddleware({ interruptOn })` | Needs a checkpointer; see The HITL path below |
| Trusted per-run values | `contextSchema` on `createAgent`/`StateGraph` → `runtime.context` | `configurable` is the older path; the AG-UI adapter drops `configurable` keys outside the schema |
| Tests without upstreams | `toolEmulatorMiddleware` | Tests only |
| CopilotKit state/actions in an agent | `copilotkitMiddleware` / `CopilotKitStateAnnotation` (`@copilotkit/sdk-js/langgraph`) | |
| Runtime + adapter | `CopilotRuntime` (`@copilotkit/runtime/v2`) + `LangGraphAgent` (`@ag-ui/langgraph`) | Node only |
| Run lifecycle in the runtime | `AgentRunner`: `InMemoryAgentRunner` (default), `SqliteAgentRunner` (`@copilotkit/sqlite-runner`) | `connect` re-joins a running thread after reload, `stop` cancels, `onConcurrentRun` decides a second run on a busy thread. In-memory is per process: several instances need sticky routing or a durable runner |
| Checkpoints | `MemorySaver` (dev), official/community savers | Own saver = L3 |
| RAG | `@langchain/textsplitters`, provider embeddings, vector store integrations | Retrieval tool via `tool()` with a server-side filter (`/agent-rag`) |
| Semantic memory | LangGraph Store with `index: { embeddings, dims, fields }` | Namespace by trusted user id |

## Backend — Mastra (shape M, checked against mastra.ai docs on 2026-10-23)

| Need | Stock (L0/L1) | Notes |
|------|---------------|-------|
| Agent loop | `new Agent({ id, instructions, model, tools })` (`@mastra/core/agent`) | |
| Routing | supervisor `Agent` with `agents: { … }` | `.network()` is deprecated |
| Fixed steps | `createWorkflow` + `createStep` | `.then` / `.branch` / `.parallel` |
| Approval of tool calls | `requireApproval: true`, or `suspend()` + `resumeSchema` | Needs `storage` |
| Input/output guards, PII | `inputProcessors` / `outputProcessors` | Order is a contract |
| Cross-tool audit | `hooks.beforeToolCall` / `afterToolCall` | |
| Trusted identity | `RequestContext` + `MASTRA_RESOURCE_ID_KEY`, `requestContextSchema` | Server-set; overrides client values |
| Threads, memory | `Memory` + a storage adapter (`@mastra/libsql`, `@mastra/pg`) | |
| Trace masking | `Observability` + `SensitiveDataFilter` | |
| Runtime + adapter | `@ag-ui/mastra`: `MastraAgent.getLocalAgents({ mastra })` or `registerCopilotKit` | |
| Model fallback | none built in | `models.ts` factory or a gateway = L2 |
| RAG | `MDocument` + `.chunk()`, `rerank()` (`@mastra/rag`), vector stores (`@mastra/pg` `PgVector`, `@mastra/libsql`), `createVectorQueryTool` | Tenant filter enforced in an own `createTool` (`/agent-rag`) |
| Semantic memory | `Memory({ vector, embedder, options: { semanticRecall } })` | Off by default |

## Frontend (`@copilotkit/react-core/v2`)

`CopilotKit` · `CopilotChat` · `useAgent` · `useAgentContext` · `useFrontendTool` · `useRenderTool` · `useHumanInTheLoop` · `useInterrupt` · `useConfigureSuggestions` · `useThreads` · `useCopilotKit` (`setHeaders`) · `useAttachments` (also `CopilotChat`'s `attachments` prop; v1 `imageUploadsEnabled` is gone).

Other clients: `@copilotkit/react-native` (same v2 hooks on mobile), Vue and Angular packages, and chat channels (`@copilotkit/channels` + `channels-slack` / `-teams` / `-discord` / `-whatsapp`) — confirm flow in `/agent-hitl` Step 4.

Testing: `@copilotkit/aimock` (`AGUIMock`) records and replays AG-UI streams for e2e.

## The HITL path (stock on AG-UI ≥ 1.0)

- **Shapes A/B:** `interrupt(value)` inside the tool (or `humanInTheLoopMiddleware`) with `reason`, `toolCallId`, `message`, `expiresAt` in the value → `@ag-ui/langgraph` emits the standard `RUN_FINISHED` interrupt outcome → `useInterrupt({ render, agentId })` renders the card and calls `resolve(payload)` / `cancel()` → the next run carries `RunAgentInput.resume[]` → `Command({ resume })`.
- **Shape M:** `requireApproval: true` surfaces as reason `mastra:tool_approval` and resumes on `true` / `{ approved: true }` (`@ag-ui/mastra` ≥ 2, one interrupt per run); `suspend()` with `resumeSchema` for richer payloads.
- `useHumanInTheLoop` is model-initiated (the model decides whether to ask): fine for clarifying questions, never a mutation gate.
- What stays custom (L2): the pending-action record keyed by the interrupt id — audit, one confirm wins, "not applied" when the upstream write failed (`/agent-hitl`).
- **0.x stacks** (AG-UI < 1.0, older adapters): the interrupt came as a `CUSTOM` event and the gate needed a decision endpoint plus a headless renderer; keep that only until the stack is upgraded.

## Vendor packs (optional)

Basic API how-tos: `langchain-ai/langchain-skills` (fundamentals, middleware, persistence, HITL, CLI) and CopilotKit's `skills/` (v2 setup, AG-UI, debugging). Use them when installed; these `agent-*` skills carry only the production invariants.
