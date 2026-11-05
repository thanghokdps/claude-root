---
type: regex
target:
  source: file
  path: src/langchain/server/agent-api.ts
pattern: "x-api-key.*callerFromHeaders.*not_found"
flags: s
---

The agent server's own routes need the internal token and a verified caller, and anything outside the thread routes is closed.
