# Motion in React Native — read before adding any animation

Most native UI should not animate; the platform already does. Adapted from expo/skills `expo-animation` (MIT), reworded. Checked against React Native 0.88 and Reanimated docs on 2026-11-04.

## 1. Should it animate?

| How often the user sees it                                 | Decision                                        |
| ---------------------------------------------------------- | ----------------------------------------------- |
| Constantly: tab switches, keyboard, scrolling, toggles     | None. The platform's behaviour or nothing       |
| Often: press feedback, row selection, list navigation      | Barely visible, under 150ms, or none            |
| Sometimes: sheets, toasts, onboarding steps                | Standard, from the Motion tokens in `DESIGN.md` |
| Rarely: first run, a success worth marking, an empty state | The one place delight is allowed                |

Tabs are peers, so switching never slides. Name the purpose in one word before writing it: feedback, continuity, state, or delight (rare tier only). No word, no animation.

## 2. Pick the cheapest tool that works

- Screen transitions, sheets, large titles, tabs, pull to refresh: the navigator's and platform's own, never rebuilt in JS.
- Anything a finger drives, or anything derived from scroll: a gesture with shared values on the UI thread (Reanimated, if the repo has it). A `setState` per frame stutters as soon as the app does anything else.
- Elements animate `transform` and `opacity`; animated layout sizes drop frames on slow phones.
- A gesture can be interrupted and keeps the finger's velocity when it hands off to the animation.

For current API details on Expo, use `expo-animation` (expo, if installed). The official plugin tracks each SDK; this file does not.

## 3. Reduced motion ships with it

Read the setting with `AccessibilityInfo.isReduceMotionEnabled()` and the `reduceMotionChanged` event, or Reanimated's `useReducedMotion()`, which reports the setting as it was when the app started. Remove movement or replace it with a short fade; state changes still show.

## 4. Judge it on a device

Feel is judged on a release build on the slowest device supported. A simulator or a dev build proves only that it runs; say so in the report.
