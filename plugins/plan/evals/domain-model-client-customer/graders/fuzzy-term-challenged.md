---
type: llm
---

The skill checks the user's claim against the code instead of taking it on trust.

PASS if the reply shows it cross-checked the code: it cites `orders.py` and `invoices.py` (or `schema.sql`) as evidence that both words resolve to the same `customers` table, and flags the leftover "client" naming (`client_id` column in `orders`, the `client` variable) as the drift to rename, rather than only agreeing with the user.
FAIL if it picks Customer without reading the code, or never mentions where "client" still appears.
