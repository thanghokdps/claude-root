---
type: llm
focus:
  source: file
  path: app/routes/orders.py
---

This is `app/routes/orders.py` after the run. The app has an owner-scoped repository (`get_order(db, owner_id, order_id)`), a service that raises `AppError(404, "order_not_found", ...)`, and a thin GET route.

PASS if the new DELETE route is thin and goes through the service with the signed-in user's id as the owner (no delete by order id alone), builds no SQL in the route, answers another user's order id with 404 `order_not_found` the same as a missing one, and uses the existing `AppError` code style.
FAIL if the file has no DELETE route, if the route only checks that a session exists and deletes by id alone, answers 403 for another user's order, builds SQL in the route, or invents a second error mechanism.
