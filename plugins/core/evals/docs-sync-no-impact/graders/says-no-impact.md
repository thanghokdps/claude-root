---
type: llm
---

The branch only renames a local variable (`order` → `found`) inside `getOrder` in `src/routes/orders.ts`; no route, layer, command, dependency or convention changes.

PASS if the reply says the change has no doc impact (docs already match) and names the file it checked.
FAIL if it edits or proposes edits to `.claude/docs/` or CLAUDE.md for this change, or invents facts to add.
