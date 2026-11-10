# DESIGN — <product>

> The visual system the UI is checked against. Filled from the repo's tokens (`styles/tokens.css`, the Tailwind theme, the UI library's theme, `theme.ts`) — the code is the source; this file names it. check-ui.py reads the spacing scale and the type-scale size from here.

## Direction

| Decision               | Value                                                    |
| ---------------------- | -------------------------------------------------------- |
| Subject                | <the concrete thing the product is about>                |
| The memorable decision | <what a user notices first>                              |
| Density                | <spacious, standard or dense>                            |
| Defaults rejected      | <generated looks this product chose not to use, and why> |

## Tokens

| Role           | Token              | Value |
| -------------- | ------------------ | ----- |
| text           | `--color-fg`       | #…    |
| text, muted    | `--color-fg-muted` | #…    |
| surface        | `--color-bg`       | #…    |
| primary action | `--color-primary`  | #…    |
| danger         | `--color-danger`   | #…    |
| radius         | `--radius`         | …px   |

## Type scale

| Step    | Size / line height | Weight | Used for       |
| ------- | ------------------ | ------ | -------------- |
| display | …px / …px          | …      | page title     |
| body    | …px / …px          | 400    | body text      |
| small   | …px / …px          | 400    | captions, help |

Max distinct sizes per view: <number of steps>

## Spacing scale

`0, 4, 8, 12, 16, 24, 32, 48, 64` (px) — every padding, margin and gap is one of these.

## Elevation

Two or three levels, each named with its use. Hierarchy comes from type and grouping first.

## Motion

| Token | Duration | Used for             |
| ----- | -------- | -------------------- |
| fast  | …ms      | press, toggle, hover |
| base  | …ms      | enter and exit       |
| slow  | …ms      | large surfaces       |

The easing, and what reduced motion replaces each one with.

## Icons

The one icon set, its sizes as tokens, and outline or filled per hierarchy level.

## Dark

Only if the product has it: each token's dark value, with contrast measured for that theme, never carried over from light.

## Components

The primitives in `components/ui/` and which one owns the primary action (one per view).

## Exceptions

One-off values, each with the element that uses it and why.
