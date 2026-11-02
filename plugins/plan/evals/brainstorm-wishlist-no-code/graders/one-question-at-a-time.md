---
type: llm
---

The user gave a feature idea and no design. Brainstorming clarifies intent one question at a time, as a choice with a recommended option, and proposes nothing to build yet.

PASS if the final reply asks exactly one clarifying question about a need (for example who can see a wishlist, whether guests can save items, or whether it must survive logout), offers 2-4 options with one marked recommended, and stops to wait for the answer.
FAIL if the reply bundles several questions in one message, skips the questions and presents a finished design or approach, or contains implementation code (a schema, route or component).
