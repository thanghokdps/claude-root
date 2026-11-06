---
type: regex
target:
  source: file
  path: apps/agent/src/prompts.ts
pattern: 'OVERVIEW[\s\S]*RESPONSE[\s\S]*OUT OF SCOPE[\s\S]*CONTEXT'
---

The agent prompt has the four sections in order.
