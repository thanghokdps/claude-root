---
type: llm
---

The request names Mastra but no frontend, no layout and no model provider, so the kit's defaults apply: the pnpm + Turborepo monorepo, and OpenAI.

PASS if the plan or scaffold has `apps/web` (a Vite app), `apps/agent` with `src/mastra/` and `packages/shared`, with the CopilotKit runtime registered on the Mastra server (`registerCopilotKit` in `server.apiRoutes`), and it uses OpenAI (`OPENAI_API_KEY`) as the model provider. A blocker report (missing Node, key or git, or denied commands) is fine.
FAIL if it plans Next.js, one package with the agent inside the web app's `src/`, a separate runtime server for the web app (Hono, `@hono/node-server`, Express), or another provider chosen because its key happens to be set.
