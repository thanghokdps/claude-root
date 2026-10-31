---
type: llm
focus: trace
---

Judge the repository function the run wrote, attempted or proposed for cancelled orders (an attempted Edit or Write to `app/repositories/orders.py` counts). Existing queries there are parameterised and filter by `user_id`.

PASS if the new function takes the owner as a required argument, filters `user_id = ?` together with `cancelled_at IS NOT NULL`, uses bound parameters, and a test is written or listed showing another user's cancelled orders are not returned.
FAIL if the function can return other owners' rows (no owner argument or no owner filter), if SQL is built by string concatenation or an f-string, or if no test for the other-owner case is written or listed.
