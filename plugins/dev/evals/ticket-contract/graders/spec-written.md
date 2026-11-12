---
type: llm
focus: trace
---

The ticket's contract is personal: it lands in `specs/412-<slug>/spec.md` in the repo's state dir (`…/claude-harness/repos/<repo>-<hash>/specs/`), outside the repo. A Write or Edit tool input counts even when the sandbox denied it.

PASS if the run writes or attempts to write a `spec.md` under a `specs/412-…/` (or `specs/412/`) folder outside the repo.
FAIL if no such write is attempted, or any contract file is written under the repo, such as `docs/tickets/`.
