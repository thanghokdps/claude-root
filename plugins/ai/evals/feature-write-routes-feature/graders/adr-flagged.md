---
type: llm
focus: trace
---

The ADR's Writes/HITL line says cancelOrder is "none built yet". The judge sees the start and the end of the run, so this grades the final reply.

PASS if the run edited that ADR line to say cancelOrder is built, or its final reply names that line as still to update.
FAIL if the final reply says nothing about the ADR line while cancelOrder was built.
