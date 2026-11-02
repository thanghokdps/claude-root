---
type: llm
---

The user gave four endpoints. Before any tool code, the reply maps endpoints to tools and asks the user to confirm.

PASS if the reply shows an endpoint → tool mapping (a table or list) where: the two GET endpoints serve read tools (merged into one or kept as two, with a reason); the cancel POST is marked as a write that needs a confirm step (HITL); the admin DELETE is excluded or explicitly questioned rather than turned into a tool; and it ends by asking the user to confirm or correct the mapping.
FAIL if it writes tool code before the mapping is confirmed, turns every endpoint into its own tool without comment, or exposes the admin DELETE as a tool.
