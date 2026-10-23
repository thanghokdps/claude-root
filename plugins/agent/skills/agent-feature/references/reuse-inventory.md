# Reuse inventory — what to find before building

Grep for facts; adjust globs to the repo's layout (`apps/*`, `packages/*` in an L2 monorepo). Read each hit far enough to say what it does.

| Row | What to find | Start with |
|-----|--------------|------------|
| Tools | every tool, its registry entry, read or mutation | `rg -n "tool\(|DynamicStructuredTool|createTool" --type ts` · `rg -n "registry|mutation" -g '*tool*'` |
| Agents | each agent id, its scope line, its tools | `rg -n "createAgent\(|addNode\(|new Agent\(|createWorkflow\(" --type ts` · the `agents:` map in `new Mastra(` · system prompt files |
| Schemas, types | Zod schemas and domain types for the entities the feature touches | `rg -n "z\.object\(" --type ts` · `rg -n "type <Entity>|interface <Entity>"` |
| Upstream clients | the API/DB client per system, auth headers, error mapping | `rg -n "fetch\(|axios|createClient" --type ts` |
| HITL | interrupt contract, version, pending-action store, decision endpoint | `rg -n "interrupt\(|requireApproval|suspend\(|pendingAction|resume" --type ts` |
| Frontend | tool renderers, cards, confirm card, suggestions, agent context | `rg -n "useRenderTool|useHumanInTheLoop|useFrontendTool|useAgentContext|suggestions" --type ts` |
| Middleware | the ordered middleware list, retry/audit wrappers | `rg -n "middleware:|createMiddleware\(|toolRetryMiddleware|inputProcessors|outputProcessors" --type ts` |
| Tests, evals | fake models, recorded AG-UI streams, eval cases per agent | `rg -l "aimock|FakeListChatModel|fakeModel" ` · `evals/` |

Record each row as `path — one line on what it does`. A row with nothing: write the command that found nothing.
