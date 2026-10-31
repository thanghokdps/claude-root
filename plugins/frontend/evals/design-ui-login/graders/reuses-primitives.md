---
type: llm
focus: trace
---

Judge the login page code the run wrote or attempted to write (an attempted Edit or Write counts even when the sandbox denied it).

PASS if the page imports `Button` and `Input` from `components/ui/` and declares no raw `<button>` or `<input>` outside `components/ui/`, and uses no raw hex colour in the page code.
FAIL if the page builds its own button or input elements, creates a duplicate primitive instead of reusing the existing ones, or hard-codes hex colours.
