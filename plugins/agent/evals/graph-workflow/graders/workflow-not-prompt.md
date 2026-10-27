---
type: llm
---

The user wants a fixed order of steps (check the order, wait for approval, then write the refund) on Mastra.

PASS if the plan uses `createWorkflow` + `createStep` with typed input/output schemas, puts the approval in a step that suspends (or `requireApproval` on the write) with storage configured, and does not rely on prompt instructions for the order.
FAIL if it puts the step order in the system prompt, uses `.network()`, or writes the refund before the approval.
