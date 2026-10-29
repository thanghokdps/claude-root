---
type: llm
focus: trace
---

Judge the edits the run made to `.claude/docs/` (Edit or Write tool input).

The branch adds `POST /orders/:id/refund` in `src/routes/orders.ts` (handler `refundOrder`, returns 409 when the order is missing or already refunded) and `refund()` in `src/services/orders.ts`.

PASS if `.claude/docs/entry-points.md` gains a row for `POST /orders/:id/refund` pointing at `src/routes/orders.ts` / `refundOrder`, the existing rows stay, and no doc is rewritten wholesale (only the affected sections change).
FAIL if entry-points.md is not updated with the refund route, the route is given a wrong path or file, or a doc is regenerated from scratch.
