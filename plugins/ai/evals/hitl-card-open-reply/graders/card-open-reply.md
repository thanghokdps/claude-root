---
type: llm
---

While a confirm card is open, a message typed into the chat must reach the server as the answer to that card, and a correction must produce a new card instead of a write.

PASS if the plan sends the typed text as the resume of the open interrupt (not as a plain new message), writes only when the reply is an unconditional yes decided by a stated rule, and on "đổi sang 3 giờ chiều" writes nothing, closes the pending record, and shows a new card with the corrected time that went through the same gate (the write tool runs again).
FAIL if the typed text is sent as a plain input while the interrupt is open, if any typed text can write without such a rule, if the pending record's fields are edited in place and then written, or if the correction is applied without a new card.
