---
type: llm
focus: trace
---

An Edit or Write tool input counts even when the sandbox denied it.

PASS if the run also writes or proposes an entry for the new solution in a `docs/solutions/INDEX.md`.
FAIL if the solution file is written with no INDEX.md update.
