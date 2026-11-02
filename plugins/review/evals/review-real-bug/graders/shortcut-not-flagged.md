---
type: llm
---

`MAX_SIZE = 100` carries a comment `shortcut: fixed cap, fine while lists stay under 10k rows; make it a query param when they grow`. The product list has 30 items, far under the stated limit, so the cap is a recorded decision, not a defect.

PASS if the review does not ask to change the MAX_SIZE cap (mentioning it as a recorded decision, or not mentioning it, both pass).
FAIL if it lists the hard-coded cap as a finding to fix (e.g. "make MAX_SIZE configurable", "magic number").
