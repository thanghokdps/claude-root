---
type: llm
---

This run scaffolded real files. Judge only the files the run wrote or edited (Write and Edit inputs, and Bash output of `grep`, `cat`, `eslint`), never the skill and reference text it read.

PASS if all hold: (a) no written file imports from `@copilotkit/runtime/langgraph` or `hono/vercel`, and the runtime's `LangGraphAgent` comes from `@ag-ui/langgraph`; (b) an `eslint.config.*` enables `@typescript-eslint/no-deprecated` and the run linted the agent folder `src/langchain` itself; (c) the closing message names the LangGraph Studio URL that `langgraph dev` prints, or states that the dev server could not start because the user must create `.env` from `.env.example` and add the OpenAI key.
FAIL if any written file has a deprecated import, lint covers only the web code, or the run wrote no files.
