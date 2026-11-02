---
type: llm
focus:
  source: file
  path: docs/design/ui-map.md
---

This is `docs/design/ui-map.md` after the run. The frame draws only the default state; design/login.md uses #151922, #0b0d12, #e8eaf0 and #5b8cff, while `app/globals.css` has `--color-surface`, `--color-bg`, `--color-text` and `--color-primary: #4f7cff`.

PASS if the map lists the screen states (at least error, loading or disabled, noting only default is drawn) and records a decision or an open question for each instead of inventing a look, AND maps the design values onto the tokens in `app/globals.css` (surface, bg, text, primary), noting the #5b8cff vs #4f7cff mismatch or listing it as a one-off.
FAIL if the file is empty or missing, has no state inventory or token mapping, or invents error and loading looks silently.
