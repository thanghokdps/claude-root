---
model: opus
effort: high
name: agent-hitl
description: Puts an agent mutation behind a human-in-the-loop confirmation (LangGraph interrupt or Mastra tool approval / suspend-resume), with a versioned interrupt contract, a pending-action record, confirm / cancel / replay resume, picking the right target record, and how web, mobile or chat clients render the confirm card. Use when an agent tool creates, updates or deletes data, or a confirm or cancel flow misbehaves. A whole new user feature that includes a write starts at agent-feature, which hands the write here.
when_to_use: agent action that writes data, "confirm before saving", confirm card, approve or reject, interrupt and resume, pending action, "tìm để xóa", add/remove/edit user via chat, resume loops or double-executes
---

# agent-hitl

**Invoke:** `/agent-hitl <the write the agent should perform>`

A mutation is decided by a human, executed once, and reported truthfully. Interrupt rules: `${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` (A/B) or `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md` (M); tool rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`; stream rules: `${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`.

---

## Step 1 — Detect the existing gate

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`, then look for an existing interrupt contract, pending-action store and decision endpoint. Reuse them; a second HITL mechanism in one repo is a defect.

No gate yet → read "The HITL gap" in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/stock-map.md` and choose: stock `humanInTheLoopMiddleware` (shape A) or `interrupt()` inside the tool (either shape). Shape M: `suspend()` inside the tool with `suspendSchema` / `resumeSchema` carrying the pending-action contract, or `requireApproval: true` when the plain approve/decline is enough. Both need `storage`. `useHumanInTheLoop` alone is never the gate.

**Done when:** the gate mechanism, the store and the resume path are named with file paths.

## Step 2 — Resolve the target before asking

The confirm card names exactly one target. Resolve it first:

- Search every list the action can apply to (for example both members and managers), not just the first.
- 0 matches → say so and stop. 1 → continue. ≥2 → ask which one, listing distinguishing fields; never pick.
- Several targets in one request: split on `,` `;` `&` and "and"/"và"; resolve each; confirm the batch as one card or one card each — follow the existing pattern.
- Permission is checked here, above the interrupt, as a short deterministic answer.
- Follow-up inputs (an image, a date) are asked only after the target is fixed.

**Done when:** tests cover 0 / 1 / ≥2 matches, a multi-target split, and a forbidden caller.

## Step 3 — The gate

Order inside the mutation:

1. Validate and authorise (may end the turn with a question; no writes).
2. Deterministic pending-action id from (thread, tool call); persist the pending-action record — the **only** write above the interrupt.
3. `interrupt(value)` (shape M: `return await context.agent.suspend(value)`, and always `return` it) with a strict, versioned value: `{ version, pendingActionId, actionType, summary, toolCallId }`.
4. Below the interrupt (runs once, on resume): check the decision matches the id; on confirm, perform the upstream write; return an outcome `{ status: completed | cancelled, actionType, summary }` built from the upstream response.

Resume:
- Confirm → claim the pending action atomically, resume with `Command({ resume })` (shape M: `agent.resumeStream(decision, { runId })` or `approveToolCall({ runId, toolCallId })`), verify the recorded outcome, clean up.
- Cancel → mark cancelled; do not resume a graph with parallel tool calls just to cancel (it can loop).
- Replay → only when the action says it is replayable.
- One active pending action per thread; a new turn with one pending gets a clear answer, not a second card.

**Done when:** tests assert: no upstream write before confirm · confirm writes exactly once · cancel writes nothing · a second confirm is rejected · the outcome says "not applied" when the upstream write failed.

## Step 4 — Client render

- Web: render from the interrupt outcome / shared state; send the decision to the resume path. See `/agent-frontend`.
- Headless client contract (mobile, chat channel): the run ends with `RUN_FINISHED` carrying the interrupt outcome; the client renders from the outcome and a versioned pending-action field in state, and resumes with `{ pendingActionId, decision }`. Chat channels that cannot keep a run pending re-emit the interrupt as a `CUSTOM` event and guard the buttons against double clicks.

**Done when:** `/agent-verify-turn` shows the interrupt outcome on one turn and the completed outcome after confirm.
