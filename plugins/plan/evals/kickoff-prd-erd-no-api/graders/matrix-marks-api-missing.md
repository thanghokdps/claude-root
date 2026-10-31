---
type: llm
focus: trace
---

Judge the reply and any write to `docs/kickoff.md` (an attempted Edit or Write counts even when the sandbox denied it).

The folder holds `docs/PRD.md` (requirements, with a Stripe payment task) and `docs/ERD.md` (data model). There is no API spec for Stripe, no tech stack, no architecture decision and no delivery doc.

PASS if a coverage matrix is shown before the first question to the user: requirements and data model rows are marked covered with a source from the two files, and the external APIs row (the Stripe spec) is marked missing or partial. Later questions target those gaps only.
FAIL if the first thing is a question with no matrix, if the matrix marks the API spec as covered, or if it asks the user for something the PRD or ERD already states (for example who the users are or which entities exist).
