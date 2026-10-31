---
type: llm
---

Each finding must come with the smallest kit change that prevents it: a skill description or when_to_use tweak (with a matching trigger case under `eval/triggers/`), a hook, or a rule.

PASS if every finding is paired with a concrete kit change (for example: extend the debugging skill's trigger so "still red after N fixes" fires it and add a trigger case; a rule or hook against a fourth edit to the same file without reading the failing test), and the report proposes the changes without claiming to have applied them.
FAIL if a finding has no kit change, the changes are vague ("improve the prompts"), or the reply says it already edited kit files.
