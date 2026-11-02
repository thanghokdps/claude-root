---
type: llm
---

Deleting a user cannot be undone, so the confirmation must be enforced by the server, not by the UI.

PASS if the plan pauses the run on the server before the delete call and runs the delete only after an explicit approve sent back into that run; a reject, a closed card or an abandoned thread deletes nothing. It must also cover at least one of: the card shows who will be deleted from a record the server looked up (not the model's wording), or approving twice deletes at most once.
FAIL if the delete is executed before the decision, if the only gate is a frontend dialog or a prompt instruction, or if a missing decision falls through to deleting.
