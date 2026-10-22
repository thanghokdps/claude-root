# Stock map — L0 building blocks

Verified against vendor docs on 2026-10-16. Docs for these packages disagree across versions: before relying on a row, confirm the export exists in the **installed** package (`node_modules/<pkg>/package.json` → `exports`, or grep its `.d.ts`).

## Backend

| Need | Stock (L0/L1) | Notes |
|------|---------------|-------|
| Agent loop | `createAgent` (`langchain`) | Usable as a node/subgraph inside a `StateGraph` |
| Retry tool calls | `toolRetryMiddleware({ tools, retryOn, maxRetries })` | Pass read tools only — mutations are never retried |
| Retry model calls | `modelRetryMiddleware` | |
| Provider fallback | `modelFallbackMiddleware(...models)` | Place last so a fallback retries the fully decorated request |
| Long threads | `summarizationMiddleware({ model, trigger, keep })` | Give the summary model message emission off, or the summary shows as a chat bubble |
| Old tool output bloat | `contextEditingMiddleware` | Clears old tool results past a token trigger |
| Runaway loops / cost | `modelCallLimitMiddleware`, `toolCallLimitMiddleware` | Thread limits need a checkpointer |
| PII | `piiMiddleware({ strategy })` | Complements trace masking; not a substitute |
| Too many tools | `llmToolSelectorMiddleware({ maxTools, alwaysInclude })` | Or route to sub-agents |
| Approval of tool calls | `humanInTheLoopMiddleware({ interruptOn })` | Needs a checkpointer; see HITL gap below |
| Tests without upstreams | `toolEmulatorMiddleware` | Tests only |
| CopilotKit state/actions in an agent | `copilotkitMiddleware` / `CopilotKitStateAnnotation` (`@copilotkit/sdk-js/langgraph`) | |
| Runtime + adapter | `CopilotRuntime` (`@copilotkit/runtime/v2`) + `LangGraphAgent` (`@ag-ui/langgraph`) | Node only |
| Checkpoints | `MemorySaver` (dev), official/community savers | Own saver = L3 |

## Frontend (`@copilotkit/react-core/v2`)

`CopilotKit` · `CopilotChat` · `useAgent` · `useAgentContext` · `useFrontendTool` · `useRenderTool` · `useHumanInTheLoop` · `useConfigureSuggestions` · `useCopilotKit` (`setHeaders`).

Testing: `@copilotkit/aimock` (`AGUIMock`) records and replays AG-UI streams for e2e.

## The HITL gap (a justified L2/L3)

- CopilotKit documents `useInterrupt` as not supported for LangGraph TypeScript.
- `useHumanInTheLoop` is model-initiated: the model decides whether to ask. Fine for clarifying questions, never a mutation gate.
- A deterministic mutation gate is `interrupt()` (inside the tool, or `humanInTheLoopMiddleware`) → AG-UI `RUN_FINISHED` interrupt outcome → client renders from the outcome/state (headless `useAgent` + subscribe) → resume via a decision endpoint or `Command({ resume })`.

## Vendor packs (optional)

Basic API how-tos: `langchain-ai/langchain-skills` (fundamentals, middleware, persistence, HITL, CLI) and CopilotKit's `skills/` (v2 setup, AG-UI, debugging). Use them when installed; these `agent-*` skills carry only the production invariants.
