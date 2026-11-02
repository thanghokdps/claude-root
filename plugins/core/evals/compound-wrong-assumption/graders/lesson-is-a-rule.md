---
type: llm
focus: trace
---

Judge the file the run wrote or attempted to write under a `docs/solutions/` directory (project `.claude/docs/solutions/` or global `~/.claude/docs/solutions/`). An Edit or Write tool input counts even when the sandbox denied it (writes under `.claude/` are always denied there).

The lesson: `orders.created_at` holds Asia/Ho_Chi_Minh local time (UTC+7), not UTC; grouping by day without converting shifted evening orders to the next day.

PASS if a solution file exists with frontmatter (title, category, severity) and a Solution / Rule section stating an imperative, specific rule (for example: check the timezone of a timestamp column before grouping by day; created_at is UTC+7, convert before date bucketing), one learning per file.
FAIL if nothing is written or proposed under docs/solutions/, or the file only retells the story of the session ("today I spent 3 hours...") with no rule a future agent can follow.
