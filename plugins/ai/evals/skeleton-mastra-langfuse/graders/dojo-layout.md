---
type: llm
---

The request names Mastra but no frontend and no model provider, so the kit's defaults apply: the layout of `mastra-ai/ui-dojo`, and OpenAI.

PASS if the plan or scaffold puts a Vite web app and `src/mastra/` in one package, with the CopilotKit runtime registered on the Mastra server (`registerCopilotKit` in `server.apiRoutes`), and it uses OpenAI (`OPENAI_API_KEY`) as the model provider. A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it plans Next.js, a separate runtime server for the web app (Hono, `@hono/node-server`, Express), or another provider chosen because its key happens to be set.
