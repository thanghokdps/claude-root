---
type: llm
---

The request leaves several things open that change the build: how a reminder is delivered (printed on a command, a callback, a notification), what "sắp đến hạn" means (window length), time zone and format of the reminder time, and whether reminders must survive a restart (the store is in-memory only).

Judge the final reply. PASS if it ends on its open questions put to the user (as a question list or as options with a recommended one) and describes no implementation as done.
FAIL if it reports the feature as built, or never asks and builds on silent guesses about delivery, window or storage.
