---
model: opus
effort: high
name: ui-polish
description: Makes an existing web app look and feel professional without a redesign. Screenshots its screens, runs the UI detector, axe and an independent taste review, ranks the issues by what users notice, fixes at most five at the root (token, then primitive, then screen), and shows before and after with the numbers re-measured. Use when a working app looks generic, unpolished or inconsistent and no design file says how it should look.
when_to_use: UI looks unprofessional, "UI xấu quá", "giao diện chưa pro", "làm UI đẹp hơn", "polish lại giao diện", app looks generated or generic, pages feel inconsistent with each other, audit the UI of an existing app, improve the look of this page without changing behaviour
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/check-ui.py *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/compare-shots.py *)
---

# ui-polish

**Invoke:** `/ui-polish [page, flow or area; the main flow when omitted]`

Polish changes how the app looks, never what it does. A mockup to match goes to `/design-ui`; a new look for the whole product goes to `/design-direction`; broken behaviour goes to `/fix-bug`.

Everything goes in `docs/design/polish.md`: the measured baseline, the ranked issues and the result.

---

## Step 1 — Baseline

1. Detect the token layer, the primitives and the UI library, as in `/ui-feature` Step 1. Read `${CLAUDE_PLUGIN_ROOT}/references/taste.md`, and create `DESIGN.md` and `PRODUCT.md` as it says.
2. Pick the screens: the requested area, otherwise the route a new user meets first and the screen they spend longest on. Include each screen's empty, loading and error states when they can be reached.
3. Run the app and, with Playwright (MCP or `@playwright/test`), shoot each state at 320, 768 and 1440 to `design/before/<state>@<width>.png`, plus any viewport the repo names.
4. Run the detector and axe per `taste.md` sections 1 and 2, and save the output under `design/before/`.

**Done when:** every chosen state has a screenshot and detector and axe output.

## Step 2 — Independent review

Dispatch the taste reviewer per `taste.md` section 3, with only the `design/before/` screenshots, `DESIGN.md` and `PRODUCT.md`.

**Done when:** its findings are saved in `docs/design/polish.md`, kept apart from the detector's.

## Step 3 — Rank

Merge the two lists into at most five issues, most noticeable first:

1. Blocks use: contrast, keyboard, missing names, overflow at 320.
2. Breaks trust: inconsistent type, spacing, radius or colour across screens.
3. Weak hierarchy: no clear first thing, competing primary actions.
4. Generated look: `taste.md` review point 6.
5. Missing states and vague copy.

For each: the evidence (screenshot or detector row), the root cause, the fix as before → after values, and the screens it touches. Prefer a fix to one token or primitive that clears several findings over five fixes on one screen.

If a visible change needs the design system extended (a new surface step, a type level, a font), ask with `AskUserQuestion` before Step 4: stay inside the system, or add this. Never extend it silently.

**Done when:** the table is in the reply and any extension is decided.

## Step 4 — Fix at the root

Fix in order: token, then primitive, then screen. No raw hex or one-off px in a screen. Behaviour stays: existing tests are not edited to make a change pass, and a component's props change only as far as the fix needs. Any new animation passes `${CLAUDE_PLUGIN_ROOT}/references/motion.md`. Update `DESIGN.md` when a token changes.

**Done when:** format, typecheck, lint and the existing tests pass.

## Step 5 — Prove it

Shoot every Step 1 state again to `design/after/`, re-run the detector and axe, and compare side by side:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/design-ui/scripts/compare-shots.py design/before design/after design/diff --threshold 1
```

The comparison is for looking, not for passing, so its threshold is out of the way. Re-dispatch the reviewer on the `after` shots only, unanchored.

**Done when:** no blocker from rank 1 remains, the detector and axe counts did not rise, no P0/P1 finding is open without the user's acceptance, and the reply shows each issue's before and after with the old and new numbers.

---

Hand-offs: behaviour bugs found on the way → `/fix-bug` · a new visual identity → `/design-direction` · before the PR → `/verify-done` → `/review-checklist`.
