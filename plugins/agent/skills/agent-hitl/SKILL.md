---
model: opus
effort: high
name: agent-hitl
description: Puts an agent mutation behind a human-in-the-loop confirmation (LangGraph interrupt or Mastra tool approval / suspend-resume) on the standard AG-UI interrupt and resume, with a pending-action record keyed by the interrupt id, confirm / cancel / replay resume, picking the right target record, and how web, mobile or chat clients render the confirm card. Use when an agent tool creates, updates or deletes data, or a confirm or cancel flow misbehaves. A whole new user feature that includes a write starts at agent-feature, which hands the write here.
when_to_use: agent action that writes data, "confirm before saving", confirm card, approve or reject, interrupt and resume, useInterrupt, resume[], pending action, "tìm để xóa", add/remove/edit user via chat, resume loops or double-executes
---

# agent-hitl

**Invoke:** `/agent-hitl <the write the agent should perform>`

A mutation is decided by a human, executed once, and reported truthfully. Interrupt rules: `${CLAUDE_PLUGIN_ROOT}/rules/langgraph.md` (A/B) or `${CLAUDE_PLUGIN_ROOT}/rules/mastra.md` (M); tool rules: `${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`; stream rules: `${CLAUDE_PLUGIN_ROOT}/rules/agui-transport.md`.

---

## Step 1 — Detect the existing gate

Run the detection in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/shapes.md`, then look for an existing interrupt contract, pending-action store and decision endpoint. Reuse them; a second HITL mechanism in one repo is a defect.

No gate yet → read "The HITL path" in `${CLAUDE_PLUGIN_ROOT}/skills/agent-architect/references/stock-map.md`, and check the installed `@ag-ui/core` (≥ 1.0 → standard interrupt outcome) and `@copilotkit/react-core` (exports `useInterrupt`). Then choose:

- Shapes A/B: `interrupt()` inside the tool, or stock `humanInTheLoopMiddleware({ interruptOn })` when the plain approve/edit/reject card is enough.
- Shape M: `requireApproval: true` for approve/decline, or `suspend()` with `suspendSchema` / `resumeSchema` when the card needs more. Both need `storage`.
- `useHumanInTheLoop` alone is never the gate.
- Older stack (AG-UI 0.x): the interrupt arrives as a `CUSTOM` event and resumes through a decision endpoint; build that only until the stack is upgraded.

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
2. Persist the pending-action record — the **only** write above the interrupt. It stores the target, the payload the card shows, `status: pending`, and is keyed by the interrupt id (deterministic from thread + tool call when the framework lets you set it, otherwise the id the framework returns).
3. Interrupt with the fields the AG-UI interrupt carries: `interrupt({ reason: "tool_call", toolCallId, message: summary, expiresAt, pendingActionId, actionType, version })` (shape M: `return await context.agent.suspend(value)`, always `return` it). The adapter maps `reason`, `toolCallId`, `message`, `expiresAt` onto the standard interrupt; the rest reaches the client in `metadata`.
4. Below the interrupt (runs once, on resume): load the record by id, check it is still `pending` and not expired; on approve perform the upstream write; return an outcome `{ status: completed | cancelled | not_applied, actionType, summary }` built from the upstream response.

Resume:
- The client answers with `RunAgentInput.resume: [{ interruptId, status, payload }]` — approve is `resolved` + `{ approved: true }`, decline `resolved` + `{ approved: false }`, abandon `cancelled`. Shapes A/B turn it into `Command({ resume })`; shape M approves on `true` / `{ approved: true }` only.
- Claim the record atomically (`pending → applying`): a second resume with the same answer replays the stored outcome instead of writing again.
- Cancel → mark cancelled and write nothing.
- Replay → only when the action says it is replayable.
- One open interrupt per thread. Input without a `resume` while one is open is a `RUN_ERROR` under AG-UI 1.0 — turn it into a short assistant line on the client ("confirm or cancel the pending change first"), not a second card.

**Done when:** tests assert: no upstream write before approve · approve writes exactly once · a replayed resume writes nothing new · decline and cancel write nothing · an expired interrupt is refused · the outcome says "not applied" when the upstream write failed.

## Step 4 — Client render

- Web (CopilotKit v2): `useInterrupt({ agentId, render, enabled })` renders the card from the interrupt (`message`, `metadata`) and calls `resolve(payload)` or `cancel()`; it renders inside `CopilotChat` by default (`renderInChat: false` to place it yourself). Wiring stays in `/agent-frontend`.
- React Native: the same hook from `@copilotkit/react-native`.
- Other headless clients: read `RUN_FINISHED.outcome`, render from `message` / `metadata`, send the next run with `resume[]`. Unknown `reason` values render from `message`, never fail.
- Chat channels (Slack, Teams…): check what the installed channel package listens for — some renderers still expect the 0.x `CUSTOM` interrupt event while `@ag-ui/mastra` ≥ 2 no longer emits it. Only the user who asked can decide, and the buttons are guarded against double clicks.

**Done when:** `/agent-verify-turn` shows the interrupt outcome on one turn and the completed outcome after the resume run.
