---
type: llm
focus: trace
---

Judge docs/design/ui-map.md as written in the run (Write/Edit tool input) for a component inventory.

PASS if the map has a primitives table (or list) naming the reusable components the frame shows — at least the button(s), the input and the card, with their variants or sizes — and states that screens are built from these primitives in `components/ui/`.
FAIL if the map only lists chat states and theme tokens, with no reusable components, or if each element is planned as its own one-off markup.
