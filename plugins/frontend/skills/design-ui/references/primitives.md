# Primitives — from the design, classified against a UI library

The list of primitives is never fixed in advance: it is what the design actually uses, named and split the way a real UI library does it.

## 1. Pick the reference library

| Repo state | Reference |
|---|---|
| Already uses a UI library (`components.json` → shadcn/ui; `@radix-ui/*`, `@headlessui/*`, `@mui/*`, `@chakra-ui/*`, `@mantine/*`, `antd`, `react-aria-components` in `package.json`) | That library. Detected, never asked |
| None yet | Ask through `AskUserQuestion`: the library that fits the stack first with `(Recommended)` (Next.js + Tailwind → shadcn/ui on Radix), then a headless alternative (Headless UI / React Aria), then "hand-built on tokens". Record the answer in the ADR |

Read the library's component list from its installed package or its current docs, never from memory; names and coverage change between versions.

## 2. Inventory the design

- Figma component sets and variants (`get_figma_data` components / componentSets; in Chrome, the Assets panel), with how many instances each has and on which frames.
- Elements drawn without components: cluster across frames by look — same height, radius, fill and padding is one component; a near-miss (52px vs 54px) snaps to one variant and the snap is recorded.
- Include the pieces designs hide in plain sight: icon set and its sizes, focus rings, dividers, skeletons, tooltips, toasts, scroll areas, empty states, overlays (drawer for the mobile sidebar, dialog, menu, popover).

## 3. Classify each item

| Class | Test | Goes to |
|---|---|---|
| **Library primitive** | the reference library has a component for it (button, input, textarea, select, checkbox, switch, slider, badge, avatar, tooltip, popover, dropdown menu, dialog, sheet/drawer, tabs, accordion, toast, scroll area, separator, skeleton, command …) | `components/ui/<name>` — installed or wrapped from the library and themed with tokens; never rebuilt by hand when the library has an accessible one |
| **Design primitive** | no library equivalent, holds no domain data, used on ≥ 2 frames or by ≥ 2 features (e.g. an icon-only pill, a section label, a gradient badge) | `components/ui/<name>`, built on tokens and on library primitives where possible |
| **Feature component** | names a domain thing (conversation row, answer toolbar, upgrade tab, social sign-in) | `features/<feature>/components/`, composed only of the two classes above |

Name each primitive as the library does (`dropdown-menu`, not `options-popup`) so the next person finds it.

## 4. Record it

In `docs/design/ui-map.md`:

| Item (design name) | Class | Library component / file | Variants · sizes · states | Instances (frames) |
|---|---|---|---|---|

**Done when:** every component set and every clustered element in the frames has a row and a class, each library primitive maps to a component that exists in the installed version, and the states page shows every primitive in all its variants.
