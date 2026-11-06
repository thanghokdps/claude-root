# Brownfield audit — custom code vs stock

Report only. The audit proposes; the user decides; nothing is migrated in the same pass.

## Sweep

For each concern, find the repo's implementation and the stock equivalent from `stock-map.md`, then confirm the equivalent exists in the installed version.

| Concern              | Typical custom code to look for                                                                                                                                                                                                                                                                            |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tool retry           | `Proxy`/wrapper around `invoke` with backoff                                                                                                                                                                                                                                                               |
| Provider fallback    | a cascade chat model, or try/catch over providers                                                                                                                                                                                                                                                          |
| Summarisation        | a summarise node or pre-model hook                                                                                                                                                                                                                                                                         |
| Tool-output trimming | manual message filtering before the model call                                                                                                                                                                                                                                                             |
| Call limits          | counters in state                                                                                                                                                                                                                                                                                          |
| HITL                 | interrupt contract, pending-action ledger, resume endpoints                                                                                                                                                                                                                                                |
| Transport            | `AbstractAgent` subclass, event filtering in an adapter subclass                                                                                                                                                                                                                                           |
| Checkpoints          | own `BaseCheckpointSaver` subclass                                                                                                                                                                                                                                                                         |
| Agent loop           | hand-built `agent → tools → agent` graph with no other nodes                                                                                                                                                                                                                                               |
| Patches              | `patches/*.patch` against agent packages                                                                                                                                                                                                                                                                   |
| Deprecated imports   | `@copilotkit/runtime/langgraph` (v1 `LangGraphAgent`, `LangGraphHttpAgent` → `@ag-ui/langgraph`), `hono/vercel` (→ `createCopilotRuntimeHandler` from `@copilotkit/runtime/v2`), `.network()`; the proof is `npx eslint <agent src>` with `@typescript-eslint/no-deprecated` on, not a grep of these names |
| Prompt shape         | one prose blob, dynamic values (date, user) interpolated into the static text, no "not mine" list — against the four sections of `rules/agent-prompts.md`                                                                                                                                                  |

## Output table

| Custom code (path) | Stock equivalent | Installed? | Behaviour the stock one lacks | Parity test that would prove a swap | Verdict |
| ------------------ | ---------------- | ---------- | ----------------------------- | ----------------------------------- | ------- |

Verdicts:

- **keep** — the stock version lacks a behaviour the repo depends on (name it). This is a justified L2/L3.
- **replace candidate** — equivalent and installed; the parity test is named and is the first task of any migration.
- **unknown** — docs and installed version disagree; say what to check.

Close with the three highest-value replace candidates and the ADR entry to record keeps.
