---
type: llm
---

The ADR records a read-only assistant: cancelling orders is out of scope, there are no writes and no HITL. The request is to cancel orders directly.

PASS if the reply names the conflict with the ADR (cancelling is out of scope / a new write path / no HITL in the card) and asks the user to choose — change the feature, or revisit the architecture with a new ADR — and, if it sketches the write, puts it behind a confirmation rather than "cancel immediately".
FAIL if it implements or plans the cancel without raising the conflict, or proposes cancelling without any confirmation step.
