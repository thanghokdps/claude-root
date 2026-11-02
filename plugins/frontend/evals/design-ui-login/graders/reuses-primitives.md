---
type: llm
focus: trace
---

Judge the files the run wrote for the login page: `app/login/page.tsx` and any component it imports (the kit's code-structure rule may put the form in `features/<area>/components/`). An Edit or Write tool input counts even when the sandbox denied it.

PASS if the page, or the form component it renders, uses `Button` and `Input` from `components/ui/`, no written file outside `components/ui/` declares a raw `<button>` or `<input>`, and no written page or component hard-codes a hex colour.
FAIL if `app/login/page.tsx` is never written, a written file builds its own button or input elements, creates a duplicate primitive instead of reusing the existing ones, or hard-codes hex colours.
