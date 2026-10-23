---
paths:
  - "**/*.{ts,tsx,mts}"
  - "**/langgraph.json"
  - "**/mastra/**"
---

# Stock first (CopilotKit · AG-UI · Mastra · LangChain · LangGraph)

Climb the ladder one rung at a time, and only with a written reason:

| Rung | What | Example |
|------|------|---------|
| L0 stock | the framework's own API | `createAgent` + built-in middleware, `CopilotRuntime` + `LangGraphAgent`, Mastra `Agent` + `memory` + workflows, `useFrontendTool` |
| L1 configure | options and props of the stock API | `toolRetryMiddleware({ tools: readTools })`, `summarizationMiddleware({ trigger, keep })` |
| L2 extend | the framework's extension points | `createMiddleware({ wrapToolCall })`, a Mastra input/output processor, a custom tool renderer |
| L3 replace | subclass, own implementation, or a patch | custom `AbstractAgent` emitter, custom checkpoint saver, `patches/*.patch` |

- A climb to L2/L3 needs a reason that is a failing test or a measurement (size, latency, missing feature on the installed version). Record it in an ADR or a one-line comment naming the limitation.
- Before claiming stock support (or its absence), check the **installed** version: read `node_modules/<pkg>/package.json` and the package's exports. Vendor docs for these packages disagree with each other across versions.
- When an upgrade adds a stock equivalent of L3 code, list it as a replacement candidate with the parity test that would prove it — never swap it silently.
- For basic API usage, defer to the vendor skill packs (`langchain-ai/langchain-skills`, CopilotKit's `skills/`, mastra.ai `llms.txt`) or current docs when installed; these rules carry only the production invariants.
