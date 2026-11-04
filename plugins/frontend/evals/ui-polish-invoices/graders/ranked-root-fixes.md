---
type: llm
focus:
  source: file
  path: docs/design/polish.md
---

This is `docs/design/polish.md` after the run.

PASS if all hold: (1) it lists at most five issues, ranked, each with before and after values; (2) the low-contrast grey text is among them; (3) fixes name a token or primitive where the cause is shared, rather than patching values in the page; (4) it says what could not be measured without a browser, and does not claim screenshots or detector results it never produced.
FAIL if the file is empty or missing, if it lists more than five issues, or if it reports measured results that no tool produced.
