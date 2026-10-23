---
paths:
  - "**/*.{ts,tsx,mts}"
---

# AG-UI transport

- Tool call events in order: `TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_END → TOOL_CALL_RESULT`.
- `TOOL_CALL_END` comes **before** `TEXT_MESSAGE_END`; otherwise the client fails the run at `RUN_FINISHED`. Test with two tool calls in flight.
- Every run ends with exactly one `RUN_FINISHED` or `RUN_ERROR`, including after cancel and after a recursion/timeout landing.
- An interrupted run ends with `RUN_FINISHED` carrying an interrupt outcome (id, reason, message, toolCallId, metadata). Emit the state the client needs before it. The interrupt spec is still a draft — check the installed `@ag-ui/*` version.
- State the client reads is a contract: additive changes only, versioned when a field changes meaning. Drop `STATE_SNAPSHOT`/`RAW` payloads the client does not read — they can grow to megabytes per turn.
- Custom events (`CUSTOM`) carry a stable name and a versioned payload; a headless client (mobile, chat channel) renders from them and from shared state, not from text.
- Tool-call ids stay stable end to end (backend → stream → client dedupe → resume).
- Every agent id is a three-way contract: backend registry (the Mastra `agents` key in shape M), `langgraph.json` or `registerCopilotKit({ resourceId })` (if used), and the client's `agent` prop. Change all three together.
