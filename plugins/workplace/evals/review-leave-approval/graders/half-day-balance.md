---
type: llm
---

`src/approve.py` computes the deduction as `(end - start).days + 1`, but the request already carries `days` (0.5 for a half day, set in `src/leave.py`).

PASS if the review lists a finding that the balance deduction ignores the half-day unit, with the failing case (a half-day request on one date deducts 1.0 day, not 0.5, so the balance is short by half a day) and the fix (deduct `req["days"]`).
FAIL if it is missing, or if it only says the arithmetic "could be wrong" without the half-day case.
