# UI quality review — read by design-ui, ui-feature and ui-polish

Two kinds of pass, two lists, never merged: the **detector** (`check-ui.py` and axe, deterministic) and the **taste review** (judgment, by a separate agent that sees pictures, not code). The split and the "verify each detector hit, name the false positives" rule are adapted from pbakaus/impeccable's `audit`, `critique` and `polish` references (Apache-2.0); the review's sixth point and the copy rules from anthropics/skills `frontend-design` (Apache-2.0); the axe pass from addyosmani/agent-skills (MIT). Nothing is copied.

## 0. DESIGN.md and PRODUCT.md

Both live at the repo root; both passes read them. One missing → create it from `.claude/templates/DESIGN.template.md` / `PRODUCT.template.md` (copied there by `/project-init`, core):

- **DESIGN.md** — tokens, type scale and spacing scale read from the repo's token layer (`styles/tokens.css`, the Tailwind theme, the UI library theme, design-ui's `docs/design/ui-map.md`). Record what the code holds, even when it is messy; the detector's job is to show the drift.
- **PRODUCT.md** — who, the job and tone from `docs/requirements.md` (else the README and the spec). A line no source supports is asked with `AskUserQuestion`, never invented.

Show the created file in the reply; it is committed with the feature.

## 1. Detector

Per state, in the running app (fixture or states page): evaluate `${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/dump-ui-styles.js` and save `design/actual/<state>.ui.json`, then

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/check-ui.py design/actual/*.ui.json --scale <DESIGN.md spacing, comma-separated> --max-font-sizes <DESIGN.md type-scale steps>
```

It prints a table, writes `design/actual/check-ui.json` and exits 1 on any finding. Verify each hit against the screenshot before fixing it. Known false positives — mark them `false positive: <reason>` in the list, do not "fix" them:

| Rule       | False positive                                                                                                                                                                        |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| contrast   | text over a gradient, image or `backdrop-filter` (listed under _skipped_, check by eye); text inside an SVG or canvas the dump cannot see; a logo or brand wordmark (WCAG exempts it) |
| spacing    | `margin: auto` resolves to px; a 1–2px hairline offset; a third-party widget's own padding                                                                                            |
| target     | a target whose 24px circle hits nothing nearby (the WCAG 2.5.8 spacing exception); a control with an equivalent larger one on the same view                                           |
| font-sizes | a state that embeds user content (rich text, markdown) at its own sizes                                                                                                               |
| name       | a control whose name comes from something the dump cannot see, such as a CSS `content` label or a shadow-DOM child; axe in section 2 settles it                                       |
| focus      | a control that opens something on focus; a focus style drawn on a parent or by `:focus-within`                                                                                        |
| heading    | a heading inside embedded user content; a third-party widget's own headings                                                                                                           |

`skipped focus-not-measured` means the browser window had no focus or the page had been clicked: focus rings were not checked. Dump in a fresh page through Playwright, or press Tab first, and re-run.

Fix order for real hits: the token first, then the primitive, then the screen.

## 2. Accessibility pass — axe

Per state, in the same running app. Use the repo's `axe-core`, or add it as a dev dependency when it is missing (API checked against the axe-core docs on 2026-11-04):

```js
await page.addScriptTag({ path: "node_modules/axe-core/axe.min.js" });
const { violations } = await page.evaluate(() => axe.run());
```

Through the Playwright MCP, evaluate the text of `node_modules/axe-core/axe.min.js` in the page first, then `axe.run()`. Save the result as `design/actual/<state>.axe.json`. Violations with `impact` `critical` or `serious` are fixed; `moderate` and `minor` are listed. axe finds only what can be automated, so a keyboard walk still follows: Tab through the state, every control is reachable in reading order with a visible focus, Escape closes overlays, and focus returns to what opened them.

Motion: any animation the state has passes `${CLAUDE_PLUGIN_ROOT}/references/motion.md`, reduced motion included.

## 3. Taste review — a separate agent

Dispatch one reviewer (`model: opus`) after the screenshots exist. Give it **only**: the state screenshots (`design/actual/*.png`, plus narrow widths), `DESIGN.md` and `PRODUCT.md`. Never the code, the diff, the Figma or the detector output — it judges what a user sees, unanchored. Prompt:

> You review UI screenshots for a product described in PRODUCT.md, against the system in DESIGN.md. You cannot see code. For each state, check the six points below and return only failures, each as `[P0–P3] <state> — <what is wrong, naming the element> — <why it hurts the user in PRODUCT.md> — <concrete fix>`. P0 blocks the job, P1 confuses most users, P2 slows them, P3 is polish. At most 5 findings per state, most severe first. No praise, no "consider".

1. **Hierarchy** — in a two-second glance the eye lands on what matters most for the job; one heading level per role, same-role text looks the same, groups separated more than their members.
2. **One primary action per view** — exactly one visually dominant action; secondary actions read as secondary; no two filled buttons competing.
3. **Empty and error states give a next step** — an empty state says why it is empty and offers the action that fills it; an error says what happened in the user's words and how to recover (retry, fix the field, contact); no bare "Something went wrong" or "No data".
4. **Copy names the user's goal** — headings and buttons say what the user gets ("Book the room", "Send for approval"), not what the system does ("Submit", "Process", "Manage entities"); the vocabulary and tone are PRODUCT.md's. An action keeps one name through the flow: the "Publish" button ends in "Published". Errors do not apologise and are never vague; sentence case, plain verbs.
5. **No decorative filler** — every element carries information or an action: no stock illustration, gradient blob, icon-per-heading, placeholder stat or lorem that could sit unchanged in an unrelated product.
6. **It looks chosen, not generated** — the look follows from this product and DESIGN.md's Direction, not from defaults: identical rounded cards with one shadow, an indigo gradient, an all-caps label above every heading, equal padding at every level, numbered markers on what is not a sequence, one icon style mixed with another. Anything DESIGN.md chose on purpose is not a finding.

## 4. Report

In the reply and in `docs/design/ui-map.md` (design-ui), `docs/design/polish.md` (ui-polish) or the PR description (ui-feature), two separate lists:

```
Detector (check-ui.py, axe): N findings — fixed: … · false positive: <rule> <selector> — <reason>
Taste review: N findings — fixed: … · open: [P?] …
```

P0 and P1 taste findings are fixed before the PR, or accepted by the user and listed as open. A clean detector run is not a pass on taste.
