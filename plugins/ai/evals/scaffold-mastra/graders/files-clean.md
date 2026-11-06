---
type: llm
focus: trace
---

This run scaffolded real files. Judge only the files the run wrote or edited (Write and Edit inputs, and Bash output of `grep`, `cat`, `eslint`), never the skill and reference text it read.

PASS if all hold: (a) `apps/agent/src/mastra/index.ts` registers the CopilotKit runtime with `registerCopilotKit` in `server.apiRoutes`, and no written file starts a separate runtime server (Hono, `@hono/node-server`, Express); (b) no written file calls `.network()`; (c) an `eslint.config.*` or a preset in `packages/config` enables `@typescript-eslint/no-deprecated` and the run linted the agent folder `apps/agent/src/mastra` itself; (d) the closing message names the Studio URL as the graph view, or states that a real turn needs `.env` created from `.env.example` with the OpenAI key.
FAIL if any written file has a deprecated import, lint covers only the web code, or the run wrote no files.
