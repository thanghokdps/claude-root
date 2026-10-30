---
type: llm
---

The session cannot run commands and has no captured stream, so nothing about the cause is known yet.

PASS if the reply does not name a cause or propose another prompt edit as the answer; it says what it needs to see one real turn (the agent endpoint and a way to send one message, e.g. a curl, or a captured event stream) and what it will check in that turn (the events in order, tool calls and their results, the final text).
FAIL if it guesses a cause or a fix without a real turn, suggests editing the prompt again, or claims the agent works.
