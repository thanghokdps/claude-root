---
type: llm
focus: trace
---

This run scaffolded real files. Judge only the files the run wrote or edited (Write and Edit inputs, and Bash output of `grep`, `cat`, `eslint`), never the skill and reference text it read.

PASS if all hold: (a) no written file imports from `@copilotkit/runtime/langgraph` or `hono/vercel`, and the runtime's `LangGraphAgent` comes from `@ag-ui/langgraph`; (b) an `eslint.config.*` enables `@typescript-eslint/no-deprecated` and the run linted the agent folder `src/langchain` itself; (c) the closing message names `docs/graph.md` as the graph view (the embed server has no Studio), or states that a real turn needs `.env` created from `.env.example` with the OpenAI key.
FAIL if any written file has a deprecated import, lint covers only the web code, or the run wrote no files.
