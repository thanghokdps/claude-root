---
paths:
  - "**/*.stories.{ts,tsx}"
  - "**/.storybook/**"
  - "**/e2e/**/*.ts"
  - "**/playwright.config.ts"
  - "**/eslint.config.*"
---

# Committed UI test rules (Storybook, Playwright, axe, jsx-a11y)

`/ui-feature` checks a screen live once (`references/taste.md`); this rule is for the checks that stay in the repo and run on every change. Claims cite storybook.js.org, playwright.dev and github.com/jsx-eslint (read 2026-11-10).

## Lint: catch it before it renders

- `eslint-plugin-jsx-a11y` is on in the flat config with `jsxA11y.flatConfigs.recommended` ([jsx-a11y](https://github.com/jsx-eslint/eslint-plugin-jsx-a11y)). The shared config sets no `files`, so scope it to `**/*.{jsx,tsx}` yourself. A disabled rule needs a comment saying why.

## Storybook: one story per state

- Every shared component (`components/ui/`) has stories for its states: default, hover / focus where it differs, disabled, loading, error, empty, long text, Vietnamese text with diacritics.
- `@storybook/addon-a11y` runs axe on each story, through the Vitest addon or the test runner. Set `parameters.a11y.test: 'error'` globally so CI fails on a violation; `'todo'` is allowed only on a story with a linked ticket ([accessibility testing](https://storybook.js.org/docs/writing-tests/accessibility-testing)).
- Stories render at the product's breakpoints through `parameters.viewport.options` ([viewport](https://storybook.js.org/docs/essentials/viewport)).

## Playwright: the journeys, at every width

- One Playwright project per supported width (for example 360, 768, 1024), each with `use: { viewport: { width, height } }`. When a project spreads `...devices[...]`, put `viewport` after the spread, or the device's viewport wins ([emulation](https://playwright.dev/docs/emulation)).
- Each main screen's spec runs `new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze()` and expects `violations` to equal `[]` ([accessibility testing](https://playwright.dev/docs/accessibility-testing)).
- Keyboard journeys are specs too: the quick switcher opens with its shortcut, every action in a journey is reachable with Tab and Enter, and focus returns where it was after a dialog closes.
- Realtime specs use two browser contexts (two people): one sends, the other sees it within the target time, both after a forced reconnect.

## In CI

- Lint, Storybook a11y and Playwright are steps of the same gate script developers run locally (devops pack's `rules/ci.md`, if installed). A flaky spec is quarantined with a ticket, never retried until green.
