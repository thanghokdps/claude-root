---
type: llm
focus: trace
---

The request leaves several things open that change the build: how a reminder is delivered (printed on a command, a callback, a notification), what "sắp đến hạn" means (window length), time zone and format of the reminder time, and whether reminders must survive a restart (the store is in-memory only).

Judge from the trace. PASS if the run shows its open questions to the user (as a question list or as options with a recommended one) and no Edit or Write to `todo/` or `tests/` happened before those questions were shown (a plan, a lane or a research note is fine; an attempted implementation edit before the questions is not).
FAIL if it edits or writes implementation or test files first and only then asks, or never asks and builds on silent guesses about delivery, window or storage.
