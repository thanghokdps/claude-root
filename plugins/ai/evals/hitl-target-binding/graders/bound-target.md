---
type: llm
---

The model filled the target id itself; the write must be bound to a trusted row. The user asked only for a confirm card, so this must be raised unprompted.

PASS if the reply requires the member id to come from a row a read/search tool returned in this thread (an id the model wrote or no matching row → resolve again or ask, never write), and the confirm card's fields to be read from that server row rather than from the model's text.
FAIL if it trusts the model-supplied id after a permission check alone, or builds the card from the tool arguments.
