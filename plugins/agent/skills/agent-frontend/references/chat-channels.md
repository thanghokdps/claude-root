# Chat channels — Slack, Teams, Discord, WhatsApp as clients

Read by `/agent-frontend` and `/agent-hitl` Step 4. A channel is one more AG-UI client of the same agent: the backend, tools, HITL gate and identity rules do not change.

Package names checked against npm (`@copilotkit/channels` 0.12.0) on 2026-10-29; the channel packages are pre-1.0, so expect breaking changes between minors. Confirm each export on the **installed** packages before relying on it.

## Stock first

- Use `@copilotkit/channels` with the channel package (`channels-slack`, `-teams`, `-discord`, `-whatsapp`) before writing a bot by hand. A hand-written bridge re-implements streaming, tool cards and the interrupt round trip, and drifts on every AG-UI release.
- Check what the installed channel renderer listens for: some still expect the 0.x `CUSTOM` interrupt event, while `@ag-ui/mastra` ≥ 2 (and any adapter on AG-UI 1.0) emits the standard interrupt outcome only. A mismatch shows as a turn that ends silently with no confirm buttons.

## Identity

- Every channel user maps to one app user server-side (workspace + channel user id → app user, set up by an explicit link step). The verified mapping goes into the run context like a web token's claims (`${CLAUDE_PLUGIN_ROOT}/rules/agent-identity-and-tools.md`).
- A channel user with no link is refused with a link instruction; never fall back to a bot-wide or workspace-wide identity.
- Verify every inbound request with the platform's signature before it reaches the agent.

## Decisions (HITL)

- Only the user who asked can confirm or cancel; a click from anyone else in the channel or thread is answered privately and changes nothing.
- Buttons are guarded against double clicks: the resume is idempotent by interrupt id (`/agent-hitl` Step 3), and the message is updated to its final state after the first click.
- The resume is built server-side from the stored interrupt (id, expiry, pending-action record), never from values carried in the button payload beyond the interrupt id and the choice.

## Errors and wording

- The agent words errors, not the channel bridge: a failed turn posts the agent's short deterministic answer (forbidden, not found, try again), never a stack trace or a raw upstream status.
- Long turns post a placeholder and edit it; platforms that time out an acknowledgement (a few seconds) get the ack first and the answer asynchronously.

**Done when:** a linked and an unlinked user each run one turn in the channel's test workspace, a confirm from a second user is refused, and a double click writes once — with the AG-UI events captured by `/agent-verify-turn`.
