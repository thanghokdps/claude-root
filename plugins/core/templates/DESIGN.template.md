# DESIGN — <product>

> The visual system the UI is checked against. Filled from the repo's tokens (`styles/tokens.css`, the Tailwind theme, the UI library's theme) — the code is the source; this file names it. check-ui.py reads the spacing scale and the type-scale size from here.

## Tokens

| Role | Token | Value |
|------|-------|-------|
| text | `--color-fg` | #… |
| text, muted | `--color-fg-muted` | #… |
| surface | `--color-bg` | #… |
| primary action | `--color-primary` | #… |
| danger | `--color-danger` | #… |
| radius | `--radius` | …px |

## Type scale

| Step | Size / line height | Weight | Used for |
|------|--------------------|--------|----------|
| display | …px / …px | … | page title |
| body | …px / …px | 400 | body text |
| small | …px / …px | 400 | captions, help |

Max distinct sizes per view: <number of steps>

## Spacing scale

`0, 4, 8, 12, 16, 24, 32, 48, 64` (px) — every padding, margin and gap is one of these.

## Components

The primitives in `components/ui/` and which one owns the primary action (one per view).

## Exceptions

One-off values, each with the element that uses it and why.
