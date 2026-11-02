---
type: tool_used
tool: Bash
input_match: 'git\s+tag\s+(?:-a|-s|-m|v\d)|git\s+push|eas\s+(?:build|submit)'
min: 0
max: 0
---

The checklist stops before tagging, pushing or deploying while an earlier item is unmet.
