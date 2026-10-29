---
type: llm
focus: trace
---

Judge the change the run made, attempted, or proposed for `.claude/docs/` — an Edit or Write tool input counts even when the eval sandbox denied it (writes under `.claude/` are blocked there), and so does an exact row given in the final reply.

The branch adds `POST /orders/:id/refund` in `src/routes/orders.ts` (handler `refundOrder`, returns 409 when the order is missing or already refunded) and `refund()` in `src/services/orders.ts`.

PASS if the change to `.claude/docs/entry-points.md` adds a row for `POST /orders/:id/refund` pointing at `src/routes/orders.ts` / `refundOrder`, keeps the existing rows, and touches only the affected sections (no doc regenerated from scratch).
FAIL if no such change to entry-points.md is made, attempted or proposed, the route gets a wrong path or file, or a doc is rewritten wholesale.
