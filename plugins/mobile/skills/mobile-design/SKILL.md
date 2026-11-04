---
model: opus
effort: high
name: mobile-design
description: Gives a React Native or Expo app a real design layer — a token theme in the repo's own styling idiom, primitives with a fixed contract, contrast measured in light and dark, and an independent review of simulator screenshots against native tells. Works for a new theme, a restyle, or an audit of an app that looks generic. Use when the question is how a mobile app looks, not what a screen does. Screen behaviour goes to mobile-feature.
when_to_use: mobile app looks generic or unprofessional, "app nhìn chưa pro", "UI app xấu", "làm theme cho app", "thiết kế lại giao diện app", React Native design system, Expo theme, design tokens for a mobile app, dark mode for the app, brand colours to a mobile palette, audit a React Native UI, app looks AI-generated, does not feel native, translate a web design to native
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/contrast.py *)
---

# mobile-design

**Invoke:** `/mobile-design <new theme | restyle | audit> [screen or area]`

One visual source of truth, in the idiom the repo already uses. `/mobile-feature` builds screen behaviour on top of it. Read `${CLAUDE_PLUGIN_ROOT}/rules/react-native.md` and `${CLAUDE_PLUGIN_ROOT}/references/native-taste.md` first.

For API details that change per Expo SDK (`@expo/ui`, semantic `Color`, native tabs), use `expo-ui`, `expo-native-ui` and `expo-design-system` (expo, if installed). This skill holds the process; the official plugin holds the current API.

---

## Step 1 — Detect

| Piece      | Look for                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------ |
| Runtime    | Expo or bare, React Native version, New Architecture; `boxShadow` and `filter` need it           |
| Styling    | NativeWind, Tamagui, Restyle, Unistyles, styled-components, `makeStyles`, plain `StyleSheet`     |
| Tokens     | `theme.ts`, `src/theme/`, `constants/theme.ts`, `constants/Colors.ts`, `global.css`, `DESIGN.md` |
| Primitives | `components/ui/` or the design-system package, and how variants and sizes are expressed          |
| Libraries  | safe-area-context, Reanimated, the navigator, the icon set, the image and blur packages          |
| Platforms  | iOS, Android or both; light, dark or both                                                        |

A declared system is the source of truth: extend it in its own names, scale and format. Never put a second system beside it. Only repeated values and no theme → those values are input: take the most frequent, snapped to a 4-point grid.

**Done when:** each row names a path or "none".

## Step 2 — Direction

No direction in `DESIGN.md` for a new theme or a restyle → run `/design-direction`. For an audit, skip to Step 5 and start from what exists.

If the system is too narrow for a visible change (no surface steps, one type size), ask with `AskUserQuestion`: stay inside it, or see proposed additions first. Never extend it silently.

**Done when:** `DESIGN.md` holds the direction, or the audit is what was asked for.

## Step 3 — Tokens

Colours, spacing, type, radius, elevation and motion, in the repo's format, through one entry point:

- Spacing on one scale with distinct steps: row gap < group gap < section gap.
- Named text styles, never raw `fontSize` in a screen. At least three levels. With static font files, set the exact weight through `fontFamily`.
- Colours by role, with each role defined for each theme. Keep brand colours few.
- Two or three elevation levels. Motion durations from `${CLAUDE_PLUGIN_ROOT}/references/native-motion.md`.

Measure every text/surface and icon/surface pair, once per theme, then fix each FAIL at the token:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/contrast.py --pairs <pairs.json>
```

**Done when:** every repeated visual value is a token, the script exits 0 and its output is in the reply.

## Step 4 — Primitives

Every primitive states, in the repo's idiom:

- **Variants** for intent, added only when a real screen needs one.
- **Sizes** mapped to tokens, never to fresh numbers.
- **States**: default, pressed, disabled, loading. Pressed feedback does not shift layout. Rows highlight; buttons dim or scale slightly.
- **Style override** merged last, for layout only. A caller changing a button's colours means a variant is missing.
- **Accessibility**: role, state, and a label on icon-only controls that stays available while loading. Targets meet 44pt on iOS and 48dp on Android, with `hitSlop` when the visual is smaller.

Promote a view to a primitive when it appears on two screens, has a nameable role, and its API is smaller than its implementation. Props that describe content become `children`. Controls that already carry the platform's design language are not wrapped.

**Done when:** each primitive the screens need has the contract, and a test for its states.

## Step 5 — Review

Follow `${CLAUDE_PLUGIN_ROOT}/references/native-taste.md`: grep the tells, run the device checks with screenshots per platform and theme, then dispatch the taste reviewer with only the screenshots, `DESIGN.md` and `PRODUCT.md`.

For an audit: rank by what users notice, take the top issues (at most five), and propose each as before → after values with its measured ratio. Fix at the token first, then the primitive, then the screen, once the user has picked which to apply.

**Done when:** tests, typecheck and lint pass; both lists are in the reply and the PR description; no P0/P1 finding is open without the user's acceptance. A platform or check that could not run is named with the reason, never assumed.

---

Hand-offs: screen behaviour and states → `/mobile-feature` · the look of a new product → `/design-direction` · a Figma to match → `/design-ui` (frontend, if installed; its token and primitive steps apply, its browser diff does not) · done → `/verify-done` → `/review-checklist`.
