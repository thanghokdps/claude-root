---
type: llm
---

The request names a custom LangGraph graph but no frontend, no layout and no model provider, so the kit's defaults apply: the pnpm + Turborepo monorepo, and OpenAI.

PASS if the plan or scaffold has `apps/web` (a Vite app), `apps/agent` and `packages/shared`, with the graph in `apps/agent/src/langgraph/` (a `StateGraph` served from `server/main.ts` through the embed server), and the CopilotKit runtime served as a route on that same server, and it uses OpenAI (`OPENAI_API_KEY`) as the model provider, and the runtime's `LangGraphAgent` is imported from `@ag-ui/langgraph` (or the import is not shown yet). A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it plans Next.js, one package with the agent inside the web app's `src/`, a separate runtime server for the web app (Hono, `@hono/node-server`, Express) outside the agent folder, another provider chosen because its key happens to be set, or an import from `@copilotkit/runtime/langgraph` (the deprecated v1 entry) or `hono/vercel`.
