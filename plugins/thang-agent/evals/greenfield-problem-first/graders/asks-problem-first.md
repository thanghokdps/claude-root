---
type: llm
---

The interview asks about the problem before any technology: P1 users and why, P2 top tasks with example messages, P3 systems read or written, P4 out of scope. A question the user's message already answers is skipped — restating that reading for the user to correct is fine. A prerequisite report before the question is expected.

PASS if the reply ends on one problem question (any of P1–P4, possibly with a short follow-up on the same topic) and has not yet decided the host, framework, repo layout or model, nor written code.
FAIL if the question it ends on is about technology (hosting, Node vs edge, monorepo vs single app, which model), if it also asks a technology question, or if it starts scaffolding.
