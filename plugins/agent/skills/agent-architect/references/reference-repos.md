# Reference repos — the official layout the scaffold mirrors

The scaffold follows the framework vendor's own example, not a layout invented by the kit. Pick the row from the ADR card (Framework × Transport × Layout). Each row splits into **core**, always mirrored; **satellites**, added only when the named ADR answer asks for them; and **never copy**.

Last checked 2026-10-23. The SHA shown is the one read on that date, not a pin.

## Rows

| # | Card | Repo · path | Core (mirror) |
|---|------|-------------|---------------|
| R1 | Mastra · own server · L1/L2 | `mastra-ai/mastra` · `templates/template-starter-agent` (@35806cb) | `src/mastra/index.ts` (one `new Mastra({ agents, tools, workflows, storage, logger, observability })`), `src/mastra/{agents,tools,workflows}/`, `.env.example`, `AGENTS.md` |
| R2 | Mastra · in-process CopilotKit · L1 | `CopilotKit/CopilotKit` · `examples/integrations/mastra` (@0b264f4) | `src/mastra/{index.ts,model.ts,agents/,tools/}`, `src/agent.ts` (`MastraAgent.getLocalAgents({ mastra })` from `@ag-ui/mastra`), `src/app/api/copilotkit/` route, `src/{components,lib}` |
| R3 | Mastra · web UI conventions | `mastra-ai/ui-dojo` (@7f98937) | `src/components/ui/` (primitives), `src/components/ai-elements/` (chat parts), `src/{lib,hooks,pages}`, `@/*` alias, kebab-case files, `cn()` + cva variants |
| R4 | LangChain `createAgent` or LangGraph · CopilotKit · L1 | `CopilotKit/CopilotKit` · `examples/integrations/langgraph-js` (@0b264f4) | `agent/` as its own package (`package.json`, `langgraph.json`, `src/`) beside the Next.js `src/` with the runtime route |
| R5 | Custom LangGraph graph · agent only | `langchain-ai/react-agent-js` (siblings: `memory-agent-js`, `retrieval-agent-template-js`) | `src/<graph>/{graph.ts,state.ts,tools.ts,prompts.ts,configuration.ts}`, `langgraph.json`, tests beside the graph |
| R6 | LangGraph · L2 monorepo | `langchain-ai/js-langgraph-monorepo-example` (@fe2cf06) | `apps/<agent>/{langgraph.json,src/graph.ts,src/state.ts}`, `libs/shared`, root `turbo.json` |
| R7 | Own AG-UI emitter (shape B) | `ag-ui-protocol/ag-ui` · `integrations/{langgraph,langchain,mastra,server-starter}` | the emitter class and its server entry for the chosen framework |
| R8 | CopilotKit v2 client or runtime | `CopilotKit/CopilotKit` · `examples/v2/{react,node,node-express,runtime,interrupts-langgraph}` | provider + `agent` prop, runtime route, interrupt render pattern |

A web client is picked with the agent: R2 or R4 for the route, plus R3 conventions when the chat is built from a design (Q-D) on shadcn/Tailwind.

## Satellites — only when the card asks

| Satellite | Added when | Taken from |
|-----------|-----------|------------|
| Chat channels (Slack, Teams, Telegram) | Q2 names a channel | R2/R4 `channels.mts`, `channel-host.mts`; Mastra `channels` option |
| Storage / memory backend | Q6 answers durable threads or long-term memory | R1 `storage` (e.g. `PostgresStore`) · LangGraph checkpointer |
| Container | Q1 says container or the deploy target needs one | R2/R4 `Dockerfile`, `.dockerignore` |
| MCP routes | P3 lists an MCP server | R3 `src/mastra/copilotkit-mcp-route.ts` |
| Recorded-stream e2e | always once the first turn streams (`/agent-verify-turn`) | `CopilotKit/aimock`, R2/R4 `fixtures/` |
| Studio / editor / platform providers | the user deploys to the vendor platform | R1 `MastraEditor`, `@mastra/platform-*` |

## Never copy

Demo pages and showcase data (`showcase.json`, `welcome.ts` seeds), lockfiles (the scaffold resolves its own), `@ts-expect-error` workarounds in the reference, `cors: { origin: '*' }`, and any hard-coded agent id that is not the card's.

## Procedure (Step 4.0)

1. Resolve the row's default-branch HEAD now, with GitHub MCP `get_file_contents` or `gh api repos/<o>/<r>/commits/HEAD`, and read the core tree at that SHA. Never rebuild a tree from memory.
2. Repo archived, moved, or the path is gone → search the org (`search_repositories org:<o>`), show what was found, and choose the replacement with the user. Do not guess.
3. Mirror the folder layout, file names and entry points. Write every file yourself, under the kit rules (env schema, identity, tests at Q-T, exact pins). Never copy a whole file.
4. Conflicts: on layout and naming the reference wins. On identity, pins, test location and tracing the kit wins. Record each difference in the ADR's Decisions.
5. Write `Reference: <repo>@<sha> · <path>` on the ADR card.
