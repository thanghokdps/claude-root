---
type: llm
focus:
  source: file
  path: docs/tickets/412/spec.md
---

This is `docs/tickets/412/spec.md` after the run.

The issue does not say which columns the CSV has, the delimiter or encoding, how the admin check reaches the export, or whether "last 30 days" counts from the order date. A behaviour nobody specified is an open question, not an invented criterion. The id is 412; no other ticket id exists.

PASS if the spec lists those unspecified points as open questions or concerns (with a recommended answer), and every id it uses is 412.
FAIL if the file is empty or missing, if it silently fixes the columns, delimiter or admin mechanism as if the ticket said so, or it invents or uses any other ticket id or issue number.
