---
type: llm
focus:
  source: file
  path: app/repositories/orders.py
---

This is `app/repositories/orders.py` after the run. Existing queries there are parameterised and filter by `user_id`.

PASS if a new function for cancelled orders takes the owner as a required argument, filters `user_id = ?` together with `cancelled_at IS NOT NULL`, and binds every value (owner, limit, dates) as a parameter. A module constant such as a column list interpolated into the SQL text is not a value and does not fail.
FAIL if there is no such function, if it can return other owners' rows (no owner argument or no owner filter), or if any value — an argument, a user id, a limit — is placed into the SQL text by concatenation or an f-string instead of a bound parameter.
