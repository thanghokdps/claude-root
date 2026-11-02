---
type: llm
focus:
  source: file
  path: tests/test_orders.py
---

This is `tests/test_orders.py` after the run, the tests for the new DELETE endpoint.

One check: a test in this file sends DELETE for an order that belongs to a different user than the signed-in one, expects 404 (or 403), and afterwards asserts the order still exists or is unchanged (a GET as the owner, a repository lookup, a status check — any proof the row survived).

PASS if such a test exists, whatever else the file covers.
FAIL if no delete tests were added, there is no test for another user's order, or that test checks only the status code and never proves the row survived.
