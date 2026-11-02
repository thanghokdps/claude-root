---
type: llm
focus: trace
---

Judge the change the run made or attempted for `.claude/docs/glossary.md`. An Edit or Write tool input counts even when the eval sandbox denied it (writes under `.claude/` are always blocked there), and so does an exact entry given in the final reply.

The code uses one table, `customers` (`src/schema.sql`), called "client" in `src/orders.py` and "customer" in `src/invoices.py`. The user leans to Customer.

PASS if a glossary entry for Customer was written or attempted in `.claude/docs/glossary.md`: a one-sentence definition, a **Not:** line that says "client" is the stray alias for the same concept (not a different one), and an **In code:** line pointing at the `customers` table or the files. Terms only; no implementation notes or decisions in the glossary.
FAIL if no glossary write is attempted or proposed, if the entry keeps both words as equals, or if it records "client" as a separate concept.
