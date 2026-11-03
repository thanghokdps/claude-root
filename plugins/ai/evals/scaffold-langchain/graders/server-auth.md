---
type: regex
target:
  source: file
  path: langgraph.json
pattern: '"auth"\s*:\s*\{[^}]*"path"\s*:\s*"[^"]*auth\.ts:auth"[^}]*"disable_studio_auth"\s*:\s*true'
flags: s
---

The LangGraph server's own routes need the internal token: custom auth is registered and the Studio bypass is off.
