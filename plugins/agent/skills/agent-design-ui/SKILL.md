---
model: opus
effort: high
name: agent-design-ui
description: Turns a design — a Figma link, exported frames or a screenshot — into the chat UI of a CopilotKit v2 web assistant. Inventories every chat state, maps design tokens onto the [data-copilotkit] theme, decides stock versus custom per element (theme, CopilotChat slots, custom slot component, headless), builds each state from a fixture, and compares screenshots against the design. Use when a design for the assistant's UI is given and the chat must look like it.
when_to_use: Figma link for the chatbot, "làm UI chat theo design", "theo figma", "giống design", mockup or screenshot of the assistant, chat UI does not match the design, theme the CopilotKit chat, message bubbles or tool cards from a design, Figma MCP rate-limited or failing ("figma mcp bị limit", "đọc figma qua chrome")
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/compare-shots.py *)
---

# agent-design-ui

**Invoke:** `/agent-design-ui <figma link | design folder> [state]`

The design decides how the chat looks; the ladder decides how little code it takes. Wiring (provider, headers, tool renderers) is `/agent-frontend`; the confirm card's contract is `/agent-hitl`. Read `${CLAUDE_PLUGIN_ROOT}/rules/agent-stock-first.md` before Step 3.

Everything this skill decides goes in `docs/design/ui-map.md`; frames live in `design/frames/<state>.png`.

---

## Step 0 — Get the design

- **Figma link** → `fileKey` from `figma.com/(design|file)/<fileKey>/…`, `node-id=12-34` → `12:34`. Call the Figma MCP's `get_figma_data` with both; never fetch the whole file when a node is given. Export each frame as PNG with `download_figma_images` (frame `nodeId`, `pngScale: 2`) into `design/frames/`.
- **Figma MCP missing or failing** (no tools, `403`, `429` / plan limit — the free plan caps API calls) → say which, then:
  1. Browser tools that drive the user's Chrome available (Claude in Chrome) → read the file there, per `${CLAUDE_SKILL_DIR}/references/figma-in-browser.md`.
  2. Otherwise ask for one: Claude in Chrome (`/chrome`), PNG exports per frame plus the variables/styles, or a working MCP (`figma-developer-mcp` with `FIGMA_API_KEY`, or Figma's Dev Mode MCP). Never design from a link you cannot read.
- **Images only** → read them; any value you cannot see exactly (hex, font, size) is asked or marked *estimated* in the map.

**Done when:** `design/frames/` holds one PNG per frame, named by state, and the source (node ids or file names) is in `ui-map.md`.

## Step 1 — Inventory the states

A chat is mostly states the happy-path frame does not show. Fill the table in `ui-map.md` from `${CLAUDE_SKILL_DIR}/references/chat-states.md`: frame present, or the user's decision (*use default*, *skip*, *design later*). Ask for missing states one question at a time — never invent a look the designer did not draw.

**Done when:** every row of `chat-states.md` has a frame or a recorded decision.

## Step 2 — Tokens → theme

Map design variables (colors, type, radius, spacing, shadow) onto the v2 tokens in `${CLAUDE_SKILL_DIR}/references/copilotkit-v2-ui.md`, written as `oklch()` in one stylesheet scoped under a wrapper class around `[data-copilotkit]`. Dark tokens only if the design has a dark frame. Fonts through the framework's font loader. Record `Figma name → CSS variable` in the map.

**Done when:** every color and radius used in the frames maps to a token, or is listed as a one-off with the element that uses it.

## Step 3 — Decide per element (the ladder)

For each element in the frames pick the lowest rung that reaches the design, and record `Element | Rung | Implementation | Why` in the map:

| Rung | Use | Example |
|------|-----|---------|
| L0 | theme tokens only | colors, radius, font |
| L1 | slot as class string or props object | bubble padding, input border |
| L2 | slot as your component (same props) | avatar + name header on assistant messages |
| L3 | headless (`useAgent`, own layout) | the chat is a panel inside a custom page layout no slot can express |

An element outside the chat component (a page header above an embedded `CopilotChat`, which has no header slot) is rung **app** — plain markup, with that reason. Slot names are in `copilotkit-v2-ui.md`; confirm each exists in the installed version before using it. Backend tool calls render through `useRenderTool` (`/agent-frontend`), the confirm card through the HITL contract (`/agent-hitl`).

**Done when:** every element has a rung and a reason, and each L2/L3 row says what the rung below could not do.

## Step 4 — Build, every state without the model

Build the components, then make each inventory state reachable without a live model: a recorded AG-UI stream replayed with `@copilotkit/aimock`, or a dev-only states page (`/__design?state=<name>`) fed by fixtures. Hand wiring to `/agent-frontend` and the confirm flow to `/agent-hitl` rather than redoing them here.

**Done when:** each state in the table renders from its fixture, and typecheck, lint and tests pass.

## Step 5 — Compare with the design

Per state, with Playwright (MCP or `@playwright/test`): viewport = the frame's size in px, `deviceScaleFactor: 2` to match `pngScale: 2`, animations off, fonts loaded, screenshot the chat region to `design/actual/<state>.png`. Then:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/compare-shots.py design/frames design/actual design/diff
```

It writes a side-by-side + diff image per state and a PASS/FAIL table (default 3% of pixels; font rendering alone stays under it). Fix each FAIL at the lowest rung, re-shoot, re-run. Show the table and the worst side-by-side images in the reply.

**Done when:** every state passes, or its remaining difference is listed in the map and accepted by the user.

---

## Hand-offs

Provider, headers, renderers → `/agent-frontend` · confirm card → `/agent-hitl` · a real turn with the new UI → `/agent-verify-turn`.
