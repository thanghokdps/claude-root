---
type: llm
focus:
  source: file
  path: app/login/page.tsx
---

This is `app/login/page.tsx` after the run. The kit's code-structure rule may put the form in `features/<area>/components/`; such a component is imported here and its file is not shown.

PASS if the page either uses `Button` and `Input` from `components/ui/`, or renders a form component it imports, and this file declares no raw `<button>` or `<input>`, no duplicate primitive and no hex colour.
FAIL if the file is empty or missing, it builds its own button or input elements, or it hard-codes hex colours.
