---
type: regex
target:
  source: file
  path: apps/agent/src/mastra/prompts.ts
pattern: "INTERNAL_CANARY_"
---

The prompt carries the canary the leak eval checks.
