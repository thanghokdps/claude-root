---
type: llm
focus: trace
---

The skill must write the ticket's contract into the repo: `docs/tickets/412/intent.md`, `spec.md` and `plan.md`. The issue text is pasted in the prompt, so no tracker read is needed. Judge the attempted writes: an Edit or Write tool input counts even when the sandbox denied it.

PASS if the trace shows writes (or attempted writes) to all three of `docs/tickets/412/intent.md`, `docs/tickets/412/spec.md` and `docs/tickets/412/plan.md`, with intent.md quoting the issue text and spec.md holding the three criteria as Given/When/Then.
FAIL if any of the three files is missing from the writes, the contract is put elsewhere (for example `specs/`), or it is written from a guessed issue instead of the pasted text.
