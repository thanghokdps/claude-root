---
type: llm
focus:
  source: file
  path: docs/design/ui-map.md
---

Judge the content of docs/design/ui-map.md.

PASS if all hold:
- It has a states table covering the states beyond the one frame (at least streaming, tool running, tool failed, error) each marked as a decision such as "use default", not invented designs.
- It maps the design's colors and radii (brand #4F46E5 or its oklch, bubble/card/input/chip radii) to CSS variables, or lists a value as a one-off with the element that uses it.
- It says, with a reason, how each visible element is built: header, user bubble, assistant bubble, order card, suggestion chips, input — theme variables only, a slot or prop of the stock chat, a custom component, or outside the chat component. Any labels are fine as long as the choice and reason are clear. The order card is a tool result rendered through useRenderTool, not a theme change.
FAIL if a states table is missing, colors are mapped without the design's values, or an element has no build choice.
