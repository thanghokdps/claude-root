---
paths:
  - "**/package.json"
  - "**/pnpm-workspace.yaml"
  - "**/patches/**"
---

# Agent stack dependencies

- Pin `@copilotkit/*`, `@ag-ui/*`, `@mastra/*` and `@langchain/langgraph-api` exactly (no `^`/`~`): their wire formats change in patch releases.
- Force a single installed copy of `@langchain/core`, `@langchain/langgraph` and `langchain` (or `@mastra/core` in shape M) (pnpm `overrides` / npm `overrides`). Two copies break `instanceof` checks and channel identity at runtime, not at compile time.
- Bump these packages together, in one change, with the evidence: typecheck, unit tests, and a real streamed turn (and the eval suite where one exists) on the new versions.
- A `patches/` entry names the upstream issue and the version it targets; re-check it on every bump and delete it when upstream fixes it.
- Check zod major compatibility (3 vs 4) against the LangGraph or Mastra version before bumping either.
- Edge/Worker bundles import only the edge-safe entry of a package; a Node-only import (`node:*`) fails at deploy, not at build.
