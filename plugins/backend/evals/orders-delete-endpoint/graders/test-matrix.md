---
type: llm
focus: trace
---

Judge the tests the run wrote, attempted or proposed for the new endpoint (an attempted Edit or Write to `tests/test_orders.py` counts even when the sandbox denied it, as does a test matrix listed in the final reply).

PASS if the matrix covers a successful delete of the caller's own order, 401 without a session, 400 or 404 for a malformed id, and a 404 for another user's order that also asserts the order still exists afterwards (the attempted write changed nothing).
FAIL if there is no test for another user's order, or the other-user test only checks the status code without proving the row survived, or no tests are written or listed at all.
