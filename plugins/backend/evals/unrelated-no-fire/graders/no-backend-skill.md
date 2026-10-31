---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?(?:api-client|api-endpoint|db-change)"'
min: 0
max: 0
arm: both
---

A plain question about an HTTP status code must not pull in a backend skill.
