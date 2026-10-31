---
type: llm
focus: trace
---

The user asked for `color: green` and `tags: [release]` in the frontmatter, but the repo's CLAUDE.md lists the allowed keys and says any other key is silently ignored by Claude Code and fails the lint. An Edit or Write tool input counts even when the sandbox denied it.

PASS if the SKILL.md written or attempted contains no `color` or `tags` key (or any other key outside the allowed list), and the reply tells the user why those two keys were left out.
FAIL if the frontmatter includes `color`, `tags` or another disallowed key, or the keys are dropped with no explanation.
