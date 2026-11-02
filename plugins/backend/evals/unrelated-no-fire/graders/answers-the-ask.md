---
type: llm
---

PASS if the reply says 409 Conflict means the request conflicts with the current state of the resource (for example a duplicate or a stale version) and gives at least one case where an API returns it.
FAIL if it confuses 409 with another status (such as 404 or 422) or gives no case for when to use it.
