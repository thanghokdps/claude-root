---
type: llm
---

The interview question is something the user can pick from, not a prose question to answer in free text.

PASS if the question the reply ends on is asked through AskUserQuestion with 2–4 options, the recommended one first and marked "(Recommended)", or — without that tool — as numbered options with one marked recommended, each option saying what it changes. Drafted answers for an open problem question (P1/P2) count as options.
FAIL if it ends on a prose question with only a "My recommendation" paragraph, or if the question shares the turn with a setup notice the answer could be mistaken for.
