---
type: llm
focus:
  source: file
  path: docs/design/ui-map.md
---

Judge docs/design/ui-map.md for a component inventory.

PASS if the map has a primitives table derived from the frame — every reusable element it shows (buttons, input, cards, chips, icons and anything else drawn), each with a class (library primitive, design primitive or feature component) and, for library primitives, the library component it maps to — and states that screens are built from these primitives in `components/ui/`.
FAIL if the map only lists chat states and theme tokens, with no reusable components, or if each element is planned as its own one-off markup.
