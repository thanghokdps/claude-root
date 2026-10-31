---
type: llm
focus: trace
---

Judge the code the run wrote or attempted to write (an attempted Edit or Write counts even when the sandbox denied it) for the display-name form that sends PATCH /api/profile.

PASS if the form handles all three: a saving state (disabled control or pending indicator), a visible error on failure announced accessibly (role="alert" or aria-live), and an optimistic update that keeps the previous name and rolls back when the PATCH fails.
FAIL if the form only fires the PATCH and shows the happy path, shows an error without restoring the previous name, or has no pending state.
