---
type: llm
focus: trace
---

Judge the SKILL.md the run wrote or attempted. An Edit or Write tool input counts even when the sandbox denied it.

PASS if the run creates `plugins/demo/skills/changelog-summary/SKILL.md` whose frontmatter has `name: changelog-summary` (equal to its directory), a `description` that says what the skill does and contains "Use when" with concrete triggers, a `when_to_use` with example phrases, and `model` and `effort`; and the body is short and steps-based.
FAIL if no SKILL.md is written or attempted, `name` differs from the directory, the description is vague or has no "Use when", or `when_to_use` is missing.
