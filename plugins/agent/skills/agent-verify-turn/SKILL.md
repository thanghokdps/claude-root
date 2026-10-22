---
model: opus
effort: high
name: agent-verify-turn
description: Proves what an AI agent actually did by driving a real chat turn and reading its AG-UI event stream, or by locating a production turn in tracing and classifying the cause — prompt, tool, model, state or infrastructure — before any fix. Use before saying an agent change works, when an agent fix still fails after retesting, or when a production answer was wrong and the cause is unknown.
when_to_use: still broken after a fix ("vẫn bị"), verify the agent turn, read the stream, run a real chat turn, prove the fix, wrong answer in production, find the trace in Langfuse or LangSmith, why did the agent say this, fix-bug red loop in an agent repo
---

# agent-verify-turn

**Invoke:** `/agent-verify-turn [local | prod-trace] <prompt or trace/thread id>`

A green unit suite does not prove a turn. The stream is the evidence: no "fixed" without it.

---

## Mode local — drive a real turn

1. **Boot** the stack the turn needs (agent server, persistence worker, upstream mocks or the dev API) with the repo's own scripts; confirm health endpoints answer.
2. **Drive** the turn through the same entry the client uses (runtime endpoint or AG-UI route) with a real, fresh auth token. An expired token looks like broken wiring — check it first.
3. **Capture** the raw event stream to a file in the scratchpad.
4. **Read** it against `${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`:
   - routing: which agent answered
   - tools: which were called, with what args, and each result
   - ordering: `TOOL_CALL_END` before `TEXT_MESSAGE_END`; exactly one `RUN_FINISHED`/`RUN_ERROR`
   - HITL: interrupt outcome present when a write is pending; nothing written before confirm
   - text: the answer matches the tool result (no claimed change that did not happen)
5. Repeat with the variations that matter: two tool calls in flight, a resumed thread, an out-of-scope prompt.

**Done when:** each expectation is marked pass/fail with the event lines that prove it, pasted in the reply.

## Mode prod-trace — classify before touching code

1. Locate the turn in the tracing provider (by thread/run id or time and user hash). Read: model and provider that answered, prompt version, tool calls and results, latency, errors.
2. Classify the cause, with the evidence line:

| Class | Signature |
|---|---|
| prompt/routing | wrong agent or tool chosen with correct inputs available |
| tool | right tool, wrong args or wrong/failed upstream result |
| model | refusal, provider error, option rejected by the model, fallback engaged |
| state | stale or duplicated messages, a pending action left open, a resumed checkpoint |
| infra | auth, timeout, deploy config, env not forwarded, tracing itself |

3. Reproduce locally with mode local using the same inputs; that reproduction is the red loop for the fix.

**Done when:** one class is named with its trace evidence and a local reproduction exists — or the trace shows the report cannot be reproduced, stated plainly.

## In a fix

This is the red loop for `/fix-bug` (dev, if installed) in an agent repo: capture the failing stream before the fix, the passing stream after. Report "fixed" only with both.
