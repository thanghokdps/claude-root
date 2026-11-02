---
type: llm
---

Question 1 is a fact: `SESSION_TTL_SECONDS = 1800` at line 4 of `app/config.py` (1800 seconds, 30 minutes).

PASS if the reply answers 1800 seconds citing `app/config.py:4` (file:line, with or without the quoted text), and does not ask the user what the TTL is.
FAIL if it answers from memory without a file and line, gives a different value, or hands this fact back to the user as a question.
