---
model: opus
effort: high
name: design-ui
description: Turns a design — a Figma link, exported frames or a screenshot — into web UI that matches it. Exports the frames, inventories every screen state, maps design variables onto tokens, classifies the design's components against the repo's UI library and builds them once as primitives, builds each state from a fixture, and compares screenshots against the design at the frame size and at narrow widths. Use when a page or screen of a web app must match its Figma or mockup.
when_to_use: Figma link for a page or screen, "làm UI theo figma", "code theo design", "giống design", mockup or screenshot to implement, page does not match the design, build the component library or tokens from Figma, Figma MCP rate-limited or failing ("figma mcp bị limit", "đọc figma qua chrome")
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/compare-shots.py *)
---

# design-ui

**Invoke:** `/design-ui <figma link | design folder> [screen]`

The design decides how the UI looks; primitives decide that each piece of it is built once. For an AI assistant's chat (CopilotKit), use `/agent-design-ui` (agent, if installed) — it runs these steps with the chat states and the CopilotKit theme.

Everything this skill decides goes in `docs/design/ui-map.md`; frames live in `design/frames/<state>.png`.

---

## Step 0 — Get the design

- **Figma link** → `fileKey` from `figma.com/(design|file)/<fileKey>/…`, `node-id=12-34` → `12:34`. Call the Figma MCP's `get_figma_data` with both; never fetch the whole file when a node is given. Export each frame as PNG with `download_figma_images` (frame `nodeId`, `pngScale: 2`) into `design/frames/`.
- **Figma MCP missing or failing** (no tools, `403`, `429` / plan limit — the free plan caps API calls) → say which, then:
  1. Browser tools that drive the user's Chrome available (Claude in Chrome) → read the file there, per `${CLAUDE_SKILL_DIR}/references/figma-in-browser.md`.
  2. Otherwise ask for one: Claude in Chrome (`/chrome`), PNG exports per frame plus the variables/styles, or a working MCP (`figma-developer-mcp` with `FIGMA_API_KEY`, or Figma's Dev Mode MCP). Never design from a link you cannot read.
- **Images only** → read them; any value you cannot see exactly (hex, font, size) is asked or marked *estimated* in the map. Estimate the font by calibration, not by eye: crop one static line of a frame (a heading or label), render the same words at the measured size in each of the 10–15 closest fonts, diff each render against the crop with `compare-shots.py`, and take the lowest; record it as *estimated (calibrated, N%)*.

**Done when:** `design/frames/` holds one PNG per frame, named by state, and the source (node ids or file names) is in `ui-map.md`.

## Step 1 — Inventory the states

Fill the table in `ui-map.md` from `${CLAUDE_SKILL_DIR}/references/screen-states.md` (plus any rows the calling skill adds): frame present, or the user's decision (*use default*, *skip*, *design later*). Ask for missing states with `AskUserQuestion` — up to 4 independent states in one call, each with options *use default (Recommended)* / *skip* / *design later* and a description of what the default looks like; numbered options when the tool is absent. Never invent a look the designer did not draw.

Record the supported viewports at the top of the map — from the ADR or spec if it has them, otherwise ask now as options (phone + desktop *(Recommended)* / desktop only / phone, tablet and desktop), stating the smallest width. Every frame being desktop-sized is not an answer.

**Done when:** every row has a frame or a recorded decision, and the viewports are recorded.

## Step 2 — Tokens

Map design variables (colors, type, radius, spacing, shadow) onto the repo's token layer — CSS variables in `styles/tokens.css`, wired into the Tailwind theme or the UI library's theme. Dark tokens only if the design has a dark frame. Fonts through the framework's font loader. Record `Figma name → token` in the map.

**Done when:** every color, radius and spacing used in the frames maps to a token, or is listed as a one-off with the element that uses it.

## Step 3 — Component inventory → primitives

Screens are built from primitives, never from raw elements, and the set of primitives comes from the design — not from a fixed list. Follow `${CLAUDE_SKILL_DIR}/references/primitives.md`:

1. **Reference library** — the UI library the repo already uses (detected), or one the user picks as options (`shadcn/ui` on Radix recommended for Next.js + Tailwind). Its component list, read from the installed package or current docs, is the vocabulary for what counts as a primitive.
2. **Inventory** — every Figma component set and variant, plus elements clustered by look across frames, overlays and icon sizes included.
3. **Classify** — library primitive (install or wrap the library's accessible component, themed with tokens) · design primitive (no library equivalent, no domain data, used on ≥ 2 frames or features) · feature component (domain-named, composed of the first two).
4. **Record** the table in the map, then build every primitive in `components/ui/` before any screen, all variants and states shown on the states page.

**Done when:** every component set and clustered element has a row and a class, each library primitive exists in the installed version, and the states page shows every primitive in all its variants.

## Step 4 — Build, every state from a fixture

Build the screens from the primitives, then make each inventory state reachable without a live backend: a dev-only states page (`/__design?state=<name>`) fed by fixtures, or mocked network (MSW, Playwright routes).

Code shape: screens and feature components compose the Step 3 primitives; feature-only pieces live under the feature that owns them; fixtures and the states page in `src/dev/`, never imported by app code; colours and sizes through tokens — no raw hex or arbitrary `[Npx]` values in components; no raw `<button>`, `<input>`, `<textarea>`, `<select>` or inline `<svg>` outside `components/ui/`; icons on one size scale; mobile-first classes.

**Done when:** each state renders from its fixture at every supported width, `grep -rnE '\[#[0-9a-fA-F]{3,8}\]' src` finds no raw colour in components, `grep -rnE '<(button|input|textarea|select)[ >]' src --include=*.tsx | grep -v components/ui/` finds nothing, and format, typecheck, lint and tests pass.

## Step 5 — Compare with the design

Per state, with Playwright (MCP or `@playwright/test`): viewport = the frame's size in px, `deviceScaleFactor: 2` to match `pngScale: 2`, animations off, fonts loaded, screenshot the frame's region to `design/actual/<state>.png`. Then:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/compare-shots.py design/frames design/actual design/diff
```

It writes a side-by-side + diff image per state and a PASS/FAIL table (default 3% of pixels; font rendering alone stays under it). Content that differs on every run by design — the agent's answer text, timestamps, avatars — goes in `design/frames/masks.json` as `{"<state>": [[x, y, w, h]]}` boxes in frame pixels: they are drawn grey and left out of the share. Mask only such content, never a component that should match. Mask every text whose words change per run — the agent's answers, titles the agent generates, the user's prompt, suggestions from data, a time-of-day greeting; text written in the code is compared pixel by pixel. Masked text is masked for its words but still checked for its look: list each such text's selector and the frame's type style (family, size, weight, line height, letter spacing, colour) in `design/frames/text-styles.json`, evaluate `${CLAUDE_SKILL_DIR}/scripts/dump-text-styles.js` in each state to write `design/actual/<state>.styles.json`, then run `python3 ${CLAUDE_SKILL_DIR}/scripts/check-text-styles.py design/frames design/actual`. Match the design as closely as it allows: 3% is the ceiling, not the goal. Once every dynamic region is masked, re-run with `--threshold 0.02` and keep fixing while the diff image shows a component offset, a wrong size or a wrong colour; what is left should be anti-aliasing only. Fix each FAIL — token first, then the primitive, then the screen — re-shoot, re-run. Show the table and the worst side-by-side images in the reply.

Then the widths no frame covers: shoot every state at the smallest supported width and one middle width (e.g. 390 and 768) to `design/actual/<state>@<width>.png`, and assert per shot `document.documentElement.scrollWidth <= window.innerWidth`, the primary action visible, and any drawer opening and closing. There is no frame to diff these against — check them against the Narrow width row, and show the narrow shots in the reply.

**Done when:** every state passes compare-shots (and check-text-styles when it has dynamic text), or its remaining difference is listed in the map and accepted by the user; and every state at each supported narrow width has no horizontal overflow and its primary action visible (unless the map marks narrow width *skip* by the user's decision).

---

## Hand-offs

Data and behaviour behind the screens → `/feature` · before the PR → `/verify-done` → `/review-checklist`.
