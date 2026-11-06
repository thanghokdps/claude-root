---
type: regex
target:
  source: file
  path: apps/agent/src/langgraph/server/agent-api.ts
pattern: "not_found.*x-api-key.*callerFromHeaders|x-api-key.*callerFromHeaders.*not_found"
flags: s
---

The agent server's own routes need the internal token and a verified caller, and anything outside the thread routes is closed.
