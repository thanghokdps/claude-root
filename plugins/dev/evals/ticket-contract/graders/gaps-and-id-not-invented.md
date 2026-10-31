---
type: llm
focus:
  source: file
  path: docs/tickets/412/spec.md
---

This is `docs/tickets/412/spec.md` after the run.

The issue does not say which columns the CSV has, the delimiter or encoding, how the admin check reaches the export, or whether "last 30 days" counts from the order date. A behaviour nobody specified is an open question, not an invented criterion. The id is 412; no other ticket id exists.

Two checks only. (1) Somewhere in the file — a Concerns table, an open-questions list, a question to the PO — the CSV columns (or the file format) appear as a point the ticket did not specify, with a recommended answer. (2) The only ticket or issue number in the file is 412 (AC1, C2 and similar row labels are not ticket numbers).

PASS if both hold, whatever else the spec decides or assumes elsewhere.
FAIL if the file is empty or missing, if no concern or question anywhere mentions the unspecified columns or format, or a ticket or issue number other than 412 appears.
