---
type: llm
focus:
  source: file
  path: app/login/page.tsx
---

This is `app/login/page.tsx` after the run, the login page.

PASS if the page imports `Button` and `Input` from `components/ui/` and declares no raw `<button>` or `<input>` outside `components/ui/`, and uses no raw hex colour in the page code.
FAIL if the file is empty or missing, if the page builds its own button or input elements, creates a duplicate primitive instead of reusing the existing ones, or hard-codes hex colours.
