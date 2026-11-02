# Screen states to inventory

Every screen the design covers gets these rows; each needs a frame or a recorded decision. The ones in **bold** are the ones designs most often leave out — and the ones users see when something goes wrong. A domain skill may add its own rows (`/agent-design-ui` adds the chat states, if installed).

| State | What it shows |
|-------|---------------|
| Default | the happy-path frame, with realistic data |
| **Empty** | no data yet: first use, nothing found after a search or filter |
| **Loading** | skeletons or spinner while data arrives; no layout shift when it lands |
| **Error / offline / unauthorised** | request failed, network lost, session expired — with the way out (retry, sign in) |
| **Long content** | long names and text wrap or truncate, many rows scroll, numbers at their widest |
| Interactive states | hover, focus-visible, active, disabled, selected — per primitive, shown on the states page |
| Overlays | each dialog, drawer, menu, popover, toast the flow opens |
| **Narrow width** | every state at the smallest supported width (and one middle width): side navigation becomes a drawer, actions stay reachable, tables and code scroll inside themselves, no horizontal page scroll, tap targets ≥ 44px |
| Dark | only if the product has dark mode |

No narrow frame is not a reason to skip the row: a desktop-sized frame describes the drawing, not a viewport decision.

Name frame files after the state in kebab-case, prefixed by the screen when there are several: `design/frames/settings-empty.png`.
