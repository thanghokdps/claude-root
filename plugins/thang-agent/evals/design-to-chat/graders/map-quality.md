---
type: llm
focus: trace
---

Judge the content of docs/design/ui-map.md as written in the run (Write/Edit tool input).

PASS if all hold:
- It has a states table covering the states beyond the one frame (at least streaming, tool running, tool failed, error) each marked as a decision such as "use default", not invented designs.
- It maps the design's colors and radii (brand #4F46E5 or its oklch, bubble/card/input/chip radii) to CSS variables, or lists a value as a one-off with the element that uses it.
- It assigns a rung (L0–L3) with a reason to the visible elements: header, user bubble, assistant bubble, order card, suggestion chips, input. The order card is a tool result rendered through useRenderTool, not a theme change. An element placed outside the chat component (e.g. a header above an embedded CopilotChat) with that reason counts as having a rung.
FAIL if a states table is missing, colors are mapped without the design's values, or elements lack rungs.
