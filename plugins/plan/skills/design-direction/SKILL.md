---
model: opus
effort: high
name: design-direction
description: Decides how a product should look before any screen is built, when there is no design to match. Grounds the look in the subject and its users, writes a short plan (palette, type, layout, density, motion, the one memorable decision), checks it against generated defaults, measures every colour pair, and records the result in DESIGN.md. In a repo with a design system it extends that system instead of adding a second one. Use when starting a new product or redesign with no Figma, or when the UI has no visual identity.
when_to_use: new app with no design, "chọn visual direction", "chọn style cho app", "chọn màu và font", "chưa có figma, thiết kế giúp tôi", "app nhìn generic quá", define the look of a product, choose a palette and typeface, create the design tokens for a new product, redesign the visual identity, before the first /ui-feature or /mobile-feature on a new product
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/contrast.py *)
---

# design-direction

**Invoke:** `/design-direction <the product, or what should change about its look>`

A direction is a decision, not a mood. "Clean and modern" decides nothing; a good direction could not be moved to an unrelated product unchanged. A Figma or mockup already decides the look: use `/design-ui` (frontend, if installed) instead.

The result goes in `DESIGN.md` at the repo root, from `.claude/templates/DESIGN.template.md` (copied by `/project-init`, core). Screens are built by `/ui-feature` (frontend, if installed) or `/mobile-design` (mobile, if installed).

---

## Step 1 — Read what exists

Look for a declared system: a `DESIGN.md`, a token file (`styles/tokens.css`, the Tailwind theme, `theme.ts`, `src/theme/`), a UI library theme (shadcn, MUI, Tamagui, Restyle, Unistyles, NativeWind), and the existing screens.

| Found                                                     | Do                                                                                                                                                                          |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing                                                   | Full freedom; go on                                                                                                                                                         |
| A system with range (surface steps, a type scale, a grid) | It is the source of truth. Extend it in its own names and format. Never add a second system beside it                                                                       |
| A system too narrow for a visible change                  | Ask with `AskUserQuestion`: work inside it (smaller, safer) or propose additions first (shown before any code). Never extend it silently, and never stay inside it silently |
| Only repeated values, no theme                            | Those values are input, not authority: take the most frequent ones, snapped to the grid                                                                                     |

**Done when:** the table's row is named, with the paths it rests on.

## Step 2 — Ground it in the subject

From `PRODUCT.md` (else `docs/requirements.md`, the README, the spec), name:

- **Subject** — the concrete thing the product is about, with its materials and vocabulary.
- **People and context** — who uses it, where, and for seconds or for hours per visit.
- **Primary job** — the one thing a screen must make easy.
- **Platforms and theme** — web, iOS, Android; light, dark or both.

A line no source supports is asked with `AskUserQuestion`, never invented. Create `PRODUCT.md` from `.claude/templates/PRODUCT.template.md` if it is missing.

**Done when:** all four are named, each from a source or the user's answer.

## Step 3 — Write the plan

A compact plan, in the reply, before any token or code:

- **Colour** — 4–6 named values with their roles (surface steps, text, accent, on-accent, danger).
- **Type** — one or two families with their roles, chosen for this subject. Sizes as a scale with at least three visibly different levels.
- **Layout** — one sentence and an ASCII wireframe for each of two candidates, then the pick and its alignment.
- **Density** — spacious, standard or dense, from the time per visit in Step 2.
- **Motion** — how much, and the one moment that gets it.
- **The one memorable decision** — what a user notices first. Spend boldness here and keep everything around it quiet.

On mobile, the platform's own type, colours and controls are a valid direction: "native, with one brand accent" is a decision. Say so rather than adding a font to look designed.

**Done when:** every bullet has a concrete value.

## Step 4 — Check it against the defaults

Read `${CLAUDE_SKILL_DIR}/references/generated-defaults.md`. For each axis the brief left free, ask whether you would have made this choice for an unrelated product. Revise what fails, and say what changed and why. The user's brief always wins, including when it asks for a listed look.

**Done when:** the reply lists each revision, or states that none was needed and why.

## Step 5 — Measure

Write every text/surface and icon/surface pair in each theme to a JSON list, then run:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/contrast.py --pairs <pairs.json>
```

Fix each FAIL in the palette and re-run. A contrast ratio is never estimated by eye.

**Done when:** the script exits 0, and its output is in the reply.

## Step 6 — Record

Fill `DESIGN.md`: the Direction section (subject, the memorable decision, defaults rejected), tokens, type scale, spacing scale, elevation, motion, icons, dark. Show the file; the user approves it before screens are built.

**Done when:** `DESIGN.md` holds every Step 3 value and the user has approved it.

---

Hand-offs: web screens → `/ui-feature` (frontend, if installed) · React Native theme and screens → `/mobile-design` (mobile, if installed) · a design to match → `/design-ui` (frontend, if installed).
