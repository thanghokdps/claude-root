---
type: llm
focus: trace
---

Ticket 412's plan records an agent decision, "Money as float in pricing.py", whose `revert:` names `src/pricing.py`. A later commit `fix: cart total off by one cent` changed `src/pricing.py` (it added rounding to the float math), so the decision settles as `changed`. Judge the ledger line the run wrote, attempted or showed in its reply: an Edit or Write input to `.claude/docs/decisions.md` counts even when the sandbox denied it (writes under `.claude/` are always denied there).

PASS if the retro reports that decision as changed (not kept, not reverted) with the fix commit as evidence, and gives a lesson of a few sentences saying what the decision assumed (two-decimal prices make float safe), what the fix commit shows it got wrong (float totals were off by a cent), and a concrete rule for the next money choice (for example Decimal or integer cents).
FAIL if the decision is missing from the retro, is marked kept or reverted, has no lesson, or has a lesson that claims more than the fix commit shows.
