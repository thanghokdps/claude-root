---
model: opus
effort: high
name: agent-design-ui
description: Styles the CopilotKit v2 chat of an AI assistant after its design — chat states (streaming, thinking, tool cards, confirm card, errors), the [data-copilotkit] theme, and stock slot versus custom component versus headless per chat element, with chat states replayed from recorded AG-UI streams. Extends /design-ui. Use when the design is for the assistant's chat.
when_to_use: Figma or mockup of the chatbot, "làm UI chat theo design", chatbot UI does not match the design, theme the CopilotKit chat, message bubbles, tool cards or confirm card from a design, chatbot Figma with the MCP limited ("figma chatbot qua chrome")
---

# agent-design-ui

**Invoke:** `/agent-design-ui <figma link | design folder> [state]`

The generic part — getting the design, tokens, primitives, building from fixtures, the screenshot diff — is `/design-ui`; follow its steps in order and add the chat-specific work below at the step it names. Wiring (provider, headers, tool renderers) is `/agent-frontend`; the confirm card's contract is `/agent-hitl`. Read `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md` before the ladder and `${CLAUDE_PLUGIN_ROOT}/rules/agent-code-structure.md` before building.

Everything goes in the same `docs/design/ui-map.md`.

---

## At /design-ui Step 1 — Chat states

A chat is mostly states the happy-path frame does not show. Add every row of `${CLAUDE_SKILL_DIR}/references/chat-states.md` to the inventory, with the same ask-as-options rule. Viewports come from the ADR (`Viewports:`, asked in `/agent-architect` Q2v).

**Done when:** every chat-state row has a frame or a recorded decision.

## At /design-ui Step 2 — Tokens → CopilotKit theme

Map the tokens onto the v2 variables in `${CLAUDE_SKILL_DIR}/references/copilotkit-v2-ui.md`, written as `oklch()` in one stylesheet scoped under a wrapper class around `[data-copilotkit]`, reading from the app's tokens rather than repeating values.

**Done when:** every colour and radius in the chat frames reaches the chat through a `[data-copilotkit]` variable or a slot class built on tokens.

## After /design-ui Step 3 — Decide per chat element (the ladder)

CopilotKit slots render the same `components/ui/` primitives. For each chat element pick the lowest rung that reaches the design, and record `Element | Rung | Implementation | Why` in the map:

| Rung | Use | Example |
|------|-----|---------|
| L0 | theme tokens only | colors, radius, font |
| L1 | slot as class string or props object | bubble padding, input border |
| L2 | slot as your component (same props) | avatar + name header on assistant messages |
| L3 | headless (`useAgent`, own layout) | the chat is a panel inside a custom page layout no slot can express |

An element outside the chat component (a page header above an embedded `CopilotChat`, which has no header slot) is rung **app** — plain markup, with that reason. Slot names are in `copilotkit-v2-ui.md`; confirm each exists in the installed version before using it. Backend tool calls render through `useRenderTool` (`/agent-frontend`), the confirm card through the HITL contract (`/agent-hitl`).

**Done when:** every chat element has a rung and a reason, and each L2/L3 row says what the rung below could not do.

## At /design-ui Step 4 — Chat states without the model

Besides the states page, a chat state can be a recorded AG-UI stream replayed with `@copilotkit/aimock` (streaming, tool running, tool failed). Hand wiring to `/agent-frontend` and the confirm flow to `/agent-hitl` rather than redoing them here.

**Done when:** each chat state renders from its fixture or recorded stream, with /design-ui Step 4's checks passing.

## At /design-ui Step 5 — Compare

Same diff and narrow-width shots; the narrow checks also assert the composer stays visible and the history drawer opens and closes. Fix each FAIL at the lowest rung.

**Done when:** /design-ui Step 5 is done for every chat state.

---

## Hand-offs

Provider, headers, renderers → `/agent-frontend` · confirm card → `/agent-hitl` · a real turn with the new UI → `/agent-verify-turn` · before the PR → `/verify-done` → `/review-checklist`.
