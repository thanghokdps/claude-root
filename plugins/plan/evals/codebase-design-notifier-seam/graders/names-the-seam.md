---
type: llm
---

`signup.py` and `billing.py` call three senders in `src/notify.py` directly, and the test patches `smtplib` because there is no seam at the notification interface. Splitting into three modules would leave three shallow modules and the same patching.

PASS if the reply answers in the deep-module vocabulary: it names where the seam goes (one notify interface that callers cross, with the senders behind it as adapters, or the dependency passed in so a test substitutes it), argues from depth or leverage (a small interface hiding the email/SMS/push detail), and applies the point that one adapter is a hypothetical seam while two are a real one, tying it to the three senders that exist. It must point at this code (`notify.py`, `signup.py`, `billing.py` or the smtplib patch).
FAIL if it gives a generic "split by responsibility" or "apply SOLID" refactor, endorses the three-module split without the seam argument, or never names the seam or the interface callers and tests share.
