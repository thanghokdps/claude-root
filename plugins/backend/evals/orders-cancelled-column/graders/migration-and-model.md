---
type: tool_used
tool: Write
input_match: '"file_path"\s*:\s*"[^"]*migrations/(?!0001)[^"]*"'
min: 1
---

The column arrives as a new migration file next to 0001; its name is the model's choice.
