---
paths:
  - "**/*.{ts,tsx,mts}"
---

# AG-UI transport

Checked against the AG-UI 1.0 spec (`@ag-ui/core` 1.0.3) on 2026-10-23. Read the installed `@ag-ui/core` version first: lines marked **0.x** apply only below 1.0.

## Events

- Tool call events in order: `TOOL_CALL_START → TOOL_CALL_ARGS → TOOL_CALL_END → TOOL_CALL_RESULT`.
- `TOOL_CALL_END` comes **before** `TEXT_MESSAGE_END`; otherwise the client fails the run at `RUN_FINISHED`. Test with two tool calls in flight.
- Every run ends with exactly one `RUN_FINISHED` or `RUN_ERROR`, including after cancel and after a recursion/timeout landing.
- Reasoning uses `REASONING_*` events; every reasoning span and message opened is closed before `RUN_FINISHED`, or the 1.0 client fails the run. **0.x:** `THINKING_*`.
- An own emitter (shape B) sets `protocolVersion: PROTOCOL_VERSION` (from `@ag-ui/core`) on `RUN_STARTED`. A proxy that forwards a producer's stream leaves that field untouched.
- Unknown properties on an event or on `RunAgentInput` are stripped by the 1.0 client. Extra data goes in `metadata` (events, messages) or `forwardedProps` (input), never in an ad-hoc field.
- Validators are imported from `@ag-ui/core/schemas` (needs zod); the main entry is types and constants only.

## Interrupts (HITL)

- An interrupted run ends with `RUN_FINISHED` and `outcome: { type: "interrupt", interrupts: [...] }`. Each interrupt has a stable `id` and a `reason` (`tool_call` with `toolCallId`, `input_required`, `confirmation`, or a namespaced `<framework>:<name>`), plus `message`, `responseSchema`, `expiresAt` and `metadata` where they apply.
- Emit the state the client needs (`STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT`) **before** that `RUN_FINISHED`.
- The client resumes with a new run on the same thread carrying `RunAgentInput.resume: [{ interruptId, status: "resolved" | "cancelled", payload? }]`. A denial is a resolved payload (`{ approved: false }`), not an error.
- One resume answers **every** open interrupt of the run. Input on a thread with an open interrupt and no `resume` → `RUN_ERROR`. A resume past `expiresAt`, with an unknown `interruptId` or a payload failing `responseSchema` → `RUN_ERROR`.
- The same `(threadId, interruptId, status, payload)` replayed is safe: it never writes twice.
- **0.x:** the interrupt arrived as a `CUSTOM` event (`on_interrupt`) and resumed through `forwardedProps.command.resume`. Adapters on 1.0 (`@ag-ui/mastra` ≥ 2) no longer emit or read it; some chat-channel renderers still do — check both installed versions.

## Messages and state

- The server's own store (checkpointer, Mastra memory) is the conversation history. `RunAgentInput.messages` is client-supplied: never trust earlier assistant or tool messages from it; take the newest user message and rebuild the rest server-side.
- User and tool content is `string | ContentPart[]`: `text`, `image`, `audio`, `video`, `document`, with `source` of type `data`, `url` or `file` (a provider file id — never fetch it as a URL). **0.x:** `InputContent` names and the `binary` part.
- State the client reads is a contract: additive changes only, versioned when a field changes meaning. Drop `STATE_SNAPSHOT`/`RAW` payloads the client does not read — they can grow to megabytes per turn.
- Custom events (`CUSTOM`) carry a stable name and a versioned payload; a headless client renders from them and from shared state, not from text.
- `RUN_FINISHED.usage[]` (model, input, output, cached and reasoning tokens) is the per-run cost record when the adapter fills it; tracing stays the source for every model call.

## Ids

- Tool-call ids stay stable end to end (backend → stream → client dedupe → resume).
- Every agent id is a three-way contract: backend registry (the Mastra `agents` key in shape M), `langgraph.json` or `registerCopilotKit({ resourceId })` (if used), and the client's `agent` prop. Change all three together.
