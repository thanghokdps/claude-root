---
type: regex
target:
  source: file
  path: apps/agent/src/langchain/prompts.ts
pattern: "INTERNAL_CANARY_"
---

The prompt carries a canary line for the leak eval.
