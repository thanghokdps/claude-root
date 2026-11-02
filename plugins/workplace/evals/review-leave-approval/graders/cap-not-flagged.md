---
type: llm
---

`MAX_PENDING = 20` in `src/leave.py` carries a comment `shortcut: fixed cap of pending requests per employee, fine for a 40-person office; make it a setting past 500 staff`. The profile has a small office, far inside the stated limit, so the cap is a recorded decision, not a defect.

PASS if the review does not ask to change the MAX_PENDING cap (mentioning it as a recorded decision, or not at all, both pass).
FAIL if it lists the hard-coded cap as a finding to fix (e.g. "make MAX_PENDING configurable", "magic number").
