---
type: tool_used
tool: Edit
input_match: '"file_path"\s*:\s*"(?![^"]*/(?:specs|docs)/)[^"]*"'
min: 0
max: 0
---

No Edit to implementation or test files before the questions are answered: only paths under `specs/` or `docs/` (a plan or research note) are allowed.
