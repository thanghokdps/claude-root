---
type: llm
focus: trace
---

Judge the files the run wrote or attempted to write (an Edit or Write input counts even when the sandbox denied it) for the settings screen.

The repo has `components/ui/button.tsx` and `input.tsx` as its primitives and CSS variables in `app/globals.css`.

PASS if the new screen imports `Button` and `Input` from `components/ui/`, uses no raw hex colour (`#rrggbb`) in the new code (CSS variables or existing classes only), and adds no raw `<button>` or `<input>` outside `components/ui/`.
FAIL if the new code declares its own `<button>` or `<input>`, contains a raw hex colour value, or ignores the existing primitives and tokens.
