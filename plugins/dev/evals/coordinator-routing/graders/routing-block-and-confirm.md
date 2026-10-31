---
type: llm
focus: trace
---

The request touches authentication (login throttling and lockout), a hard gate that forces the high-risk lane; it is a new capability.

Judge from the reply and the trace. PASS if the reply shows the routing summary with an Intent (new-feature or equivalent), the Lane high-risk, and a Routing line naming where it dispatches (for example /feature, or a Planner then Implementer then Verifier chain), and it asks to proceed before dispatching or implementing.
FAIL if the lane is tiny or normal, no routing summary appears, or it starts implementing the throttle (any Write of source code) without asking first. Writes under `specs/` are fine.
