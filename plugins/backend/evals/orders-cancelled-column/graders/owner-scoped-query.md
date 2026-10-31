---
type: llm
focus:
  source: file
  path: app/repositories/orders.py
---

This is `app/repositories/orders.py` after the run. Existing queries there are parameterised and filter by `user_id`.

PASS if a new function for cancelled orders takes the owner as a required argument, filters `user_id = ?` together with `cancelled_at IS NOT NULL`, and uses bound parameters.
FAIL if there is no such function, if it can return other owners' rows (no owner argument or no owner filter), or if SQL is built by string concatenation or an f-string.
