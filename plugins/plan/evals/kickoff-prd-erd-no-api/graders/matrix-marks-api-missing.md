---
type: llm
---

Judge the final reply.

The folder holds `docs/PRD.md` (requirements, with a Stripe payment task) and `docs/ERD.md` (data model). There is no API spec for Stripe, no tech stack, no architecture decision and no delivery doc.

PASS if a coverage matrix is shown in the reply, ahead of any question to the user: the requirements and data model rows are marked covered or partly covered with a source from the two files, and the external APIs row (the Stripe spec) is marked missing or partial (⚠️, ❌, "missing", "partial", or words to that effect all count). The question that follows may target any gap the matrix shows.
FAIL if the first thing is a question with no matrix, if the matrix marks the API spec as fully covered, or if it asks the user for something the PRD or ERD already states in full (for example who the users are).
