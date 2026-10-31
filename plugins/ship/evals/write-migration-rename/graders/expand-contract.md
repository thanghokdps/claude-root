---
type: llm
focus: trace
---

Judge the migration the run wrote, attempted or proposed — an Edit or Write tool input counts even when the sandbox denied it, and so does an exact SQL/plan given in the final reply.

The column is renamed on a live production table while old code (`src/users.ts` reads `user.fullName`) still runs during deploy.

PASS if the plan is expand/contract in separate steps: add `displayName` (nullable or defaulted), dual-write and batched idempotent backfill from `fullName`, switch reads to `displayName` in code, and drop `fullName` only in a later migration/release; and it names the down/rollback path (how to undo each step, e.g. drop the new column / keep the old one until the drop step).
FAIL if the only change is a single `ALTER TABLE ... RENAME COLUMN "fullName" TO "displayName"` (or editing the Prisma field name alone) while old code runs, if the drop is in the same migration as the add, or if no down path is mentioned.
