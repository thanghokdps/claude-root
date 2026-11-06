---
type: regex
target:
  source: file
  path: apps/agent/src/mastra/prompts.ts
pattern: 'OVERVIEW[\s\S]*RESPONSE[\s\S]*OUT OF SCOPE[\s\S]*CONTEXT'
---

The prompt has the four sections of `rules/agent-prompts.md`, in order.
