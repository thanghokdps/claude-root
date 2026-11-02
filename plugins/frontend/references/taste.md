# UI quality review — read by design-ui and ui-feature at their last step

Two passes, two lists, never merged: the **detector** (`check-ui.py`, deterministic, over computed styles) and the **taste review** (judgment, by a separate agent that sees pictures, not code). The split and the "verify each detector hit, name the false positives" rule are adapted from pbakaus/impeccable's `audit`, `critique` and `polish` references (Apache-2.0); nothing is copied.

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

| Rule | False positive |
|------|----------------|
| contrast | text over a gradient, image or `backdrop-filter` (listed under *skipped*, check by eye); text inside an SVG or canvas the dump cannot see; a logo or brand wordmark (WCAG exempts it) |
| spacing | `margin: auto` resolves to px; a 1–2px hairline offset; a third-party widget's own padding |
| target | a target whose 24px circle hits nothing nearby (the WCAG 2.5.8 spacing exception); a control with an equivalent larger one on the same view |
| font-sizes | a state that embeds user content (rich text, markdown) at its own sizes |

Fix order for real hits: the token first, then the primitive, then the screen.

## 2. Taste review — a separate agent

Dispatch one reviewer (`model: opus`) after the screenshots exist. Give it **only**: the state screenshots (`design/actual/*.png`, plus narrow widths), `DESIGN.md` and `PRODUCT.md`. Never the code, the diff, the Figma or the detector output — it judges what a user sees, unanchored. Prompt:

> You review UI screenshots for a product described in PRODUCT.md, against the system in DESIGN.md. You cannot see code. For each state, check the five points below and return only failures, each as `[P0–P3] <state> — <what is wrong, naming the element> — <why it hurts the user in PRODUCT.md> — <concrete fix>`. P0 blocks the job, P1 confuses most users, P2 slows them, P3 is polish. At most 5 findings per state, most severe first. No praise, no "consider".

1. **Hierarchy** — in a two-second glance the eye lands on what matters most for the job; one heading level per role, same-role text looks the same, groups separated more than their members.
2. **One primary action per view** — exactly one visually dominant action; secondary actions read as secondary; no two filled buttons competing.
3. **Empty and error states give a next step** — an empty state says why it is empty and offers the action that fills it; an error says what happened in the user's words and how to recover (retry, fix the field, contact); no bare "Something went wrong" or "No data".
4. **Copy names the user's goal** — headings and buttons say what the user gets ("Book the room", "Send for approval"), not what the system does ("Submit", "Process", "Manage entities"); the vocabulary and tone are PRODUCT.md's.
5. **No decorative filler** — every element carries information or an action: no stock illustration, gradient blob, icon-per-heading, placeholder stat or lorem that could sit unchanged in an unrelated product.

## 3. Report

In the reply and in `docs/design/ui-map.md` (design-ui) or the PR description (ui-feature), two separate lists:

```
Detector (check-ui.py): N findings — fixed: … · false positive: <rule> <selector> — <reason>
Taste review: N findings — fixed: … · open: [P?] …
```

P0 and P1 taste findings are fixed before the PR, or accepted by the user and listed as open. A clean detector run is not a pass on taste.
