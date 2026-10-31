---
type: llm
---

The week's history has a commit `revert: paginate order history`, `src/cart.py` changed again in the commits `fix: cart total off by one cent` and `fix: cart discount cap` (plus the feature commit before them), and ticket 412 estimated 4h with an actual of 12h (x3). There are no red CI builds, PRs or escalations in this repo.

PASS if the retro has a Hurt section where every row cites a concrete commit (subject or sha) or ticket, and it includes the revert, the repeated rework of `src/cart.py` and ticket 412's x3 estimate miss with its cause.
FAIL if any Hurt row has no commit or ticket behind it, or it invents an incident, red build or PR that the history does not contain.
