# Motion on the web — read before adding any animation

Most UI should not animate. Adapted from expo/skills `expo-animation` (MIT) and anthropics/skills `frontend-design` (Apache-2.0); reworded for the web, nothing copied.

## 1. Should it animate?

| How often the user sees it                                   | Decision                                        |
| ------------------------------------------------------------ | ----------------------------------------------- |
| Constantly: typing, tab switches, toggles, keyboard commands | None                                            |
| Often: hover, press, row selection, opening a menu           | Barely visible, under 150ms, or none            |
| Sometimes: dialogs, drawers, toasts, expanding a section     | Standard, from the Motion tokens in `DESIGN.md` |
| Rarely: first run, a success worth marking, an empty state   | The one place delight is allowed                |

## 2. Name the purpose

One word before writing it: feedback, continuity (where this came from or went), state, or delight (rare tier only). No word, no animation.

Motion that answers what the user did is welcome. Motion nobody asked for, like fade-and-slide on each section or a lift on every card, is what makes a page look generated. One orchestrated moment beats scattered effects.

## 3. Build it

- Animate `transform` and `opacity`. Width, height, top and left force layout on every frame.
- Durations and easing come from the `DESIGN.md` tokens. An exit is faster than its enter.
- Never `transition: all`: it animates whatever changes next, including properties nobody meant to move.
- An animation in progress can be interrupted: a second click reverses it from where it is, it does not queue.
- Nothing blocks input while it plays.

## 4. Reduced motion ships with it

Under `@media (prefers-reduced-motion: reduce)`, movement is removed or replaced by a short fade; state changes still show. Never hide content behind an entrance that reduced motion skips. Check it with the browser's emulation (Playwright `emulateMedia({ reducedMotion: "reduce" })`) before reporting done.
