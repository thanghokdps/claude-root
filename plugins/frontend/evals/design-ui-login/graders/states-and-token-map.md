---
type: llm
focus: trace
---

Judge the reply and any file the run wrote or attempted (an attempted Edit or Write counts even when the sandbox denied it, e.g. docs/design/ui-map.md).

The frame draws only the default state; design/login.md uses #151922, #0b0d12, #e8eaf0 and #5b8cff, while `app/globals.css` has `--color-surface`, `--color-bg`, `--color-text` and `--color-primary: #4f7cff`.

PASS if, before or alongside the code, the run lists the screen states (at least error, loading or disabled, noting only default is drawn) and asks about or records a decision for them instead of inventing a look, AND maps the design values onto the tokens in `app/globals.css` (surface, bg, text, primary), noting the #5b8cff vs #4f7cff mismatch or listing it as a one-off.
FAIL if it goes straight to code with no state inventory or token mapping, or invents error and loading looks silently.
