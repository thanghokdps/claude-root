---
type: llm
focus:
  source: file
  path: tests/test_orders.py
---

This is `tests/test_orders.py` after the run, the tests for the new DELETE endpoint.

PASS if the tests cover a successful delete of the caller's own order, 401 without a session, 400 or 404 for a malformed id, and a 404 for another user's order that also asserts the order still exists afterwards (the attempted write changed nothing).
FAIL if there is no test for another user's order, or the other-user test only checks the status code without proving the row survived, or no delete tests were added.
