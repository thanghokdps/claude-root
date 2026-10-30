---
type: llm
---

The interview asks about the problem before any technology: who uses it and why, the main things they ask with example messages, which systems it reads or writes, what is out of scope. A question the user's message already answers is skipped — restating that reading for the user to correct is fine. A prerequisite report before the question is expected.

PASS if the reply ends on one problem question (any of those topics, possibly with a short follow-up on the same topic) and has not yet decided the host, framework, repo layout or model, nor written code.
FAIL if the question it ends on is about technology (hosting, Node vs edge, monorepo vs single app, which model), if it also asks a technology or setup question (an install, a `.env` step, what to do about a missing item), or if it starts scaffolding.
