---
type: llm
focus:
  source: file
  path: docs/design/ui-map.md
---

Judge docs/design/ui-map.md for responsive coverage. The only frame is desktop-sized and the user said to use defaults for undrawn states.

PASS if the map records supported viewports or a smallest width (a number in px, or phone/tablet/desktop), and its Narrow width row is a decision tied to that width (for example "use default: below 768px the sidebar becomes a drawer, composer pinned, no horizontal scroll") rather than left blank or assumed desktop-only without saying so.
FAIL if there is no Narrow width row, no width is named anywhere, or the map treats the frame's size as the only viewport.
