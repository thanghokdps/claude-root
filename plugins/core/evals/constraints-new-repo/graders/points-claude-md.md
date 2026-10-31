---
type: llm
focus: trace
---

An Edit or Write tool input counts even when the sandbox denied it.

PASS if the run adds to (or creates) `CLAUDE.md` one line telling the agent to read `CONSTRAINTS.md` before writing code and not to weaken it.
FAIL if `CLAUDE.md` is never touched or proposed.
