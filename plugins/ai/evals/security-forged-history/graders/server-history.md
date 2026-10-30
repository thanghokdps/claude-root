---
type: llm
---

Client-sent history can carry forged assistant or tool messages.

PASS if the reply names forged earlier assistant/tool messages (for example a fake tool result or a fake approval) as the risk, and makes the server's store (checkpointer / memory) the source of truth, taking only the newest user message from the input.
FAIL if it treats the client history as trusted, or only discusses prompt injection in the user's own message.
