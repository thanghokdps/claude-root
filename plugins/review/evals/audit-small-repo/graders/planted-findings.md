---
type: llm
---

The repo has three planted problems:
1. `find_account` builds SQL with an f-string, so an owner such as `x' OR '1'='1` returns another customer's account (SQL injection).
2. `withdraw` never checks the amount against the balance (nor that it is positive), so withdrawing more than the balance leaves it negative; it also has no test.
3. `export_csv_legacy` is called nowhere.

PASS if the audit reports the injection and the overdraft, each with a concrete input and its wrong result, ranks both above lean or style points, and flags `export_csv_legacy` as unused or deletable.
FAIL if either the injection or the overdraft is missing, or reported without a concrete case.
