---
type: llm
---

The request names LangChain but no frontend and no model provider, so the kit's defaults apply: one package laid out like `mastra-ai/ui-dojo`, and OpenAI.

PASS if the plan or scaffold puts a Vite web app and the agent in one package, with the agent in `src/langchain/` (a `createAgent` graph served from `src/langchain/server/main.ts` through the embed server), and the CopilotKit runtime served as a route on that same server, and it uses OpenAI (`OPENAI_API_KEY`) as the model provider, and the runtime's `LangGraphAgent` is imported from `@ag-ui/langgraph` (or the import is not shown yet). A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it plans Next.js, a separate runtime server for the web app (Hono, `@hono/node-server`, Express) outside the agent folder, a separate `agent/` package, another provider chosen because its key happens to be set, or an import from `@copilotkit/runtime/langgraph` (the deprecated v1 entry) or `hono/vercel`.
