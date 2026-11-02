---
type: llm
---

A billing question reached the support agent, so the fault is in the routing decision, not in the support agent's answer.

PASS if the reply locates the problem at the router (how it chooses: route descriptions, the classifier prompt, or a structured routing output), proposes a fix there, and proposes checking it with a small set of billing vs support questions, the failing one included, before and after the change.
FAIL if the fix is only to tell the support agent to refuse or forward billing questions, to merge the agents, or to change models, without fixing or testing the routing decision.
