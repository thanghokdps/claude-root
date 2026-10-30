---
type: llm
focus: trace
---

The repo already has an Orders API client (`ordersApi`), an order-code schema (`OrderCode`), a tool that forwards the caller's token from `config`, an ADR whose task table names the lookup tool, and an order card that renders a tool by name. The user said none of this.

Judge the tool the run wrote, or proposed if it stopped to confirm first.
PASS if all hold:
- It calls the existing `ordersApi` for one order rather than a new fetch or HTTP client.
- Its input is validated with the existing `OrderCode` (or the same pattern), not a bare string.
- The token is passed the way `listOrders` passes it, never as a tool argument the model fills. Flagging that a token in `configurable` reaches checkpoints, as a separate change, is a plus.
- Its name matches what the ADR and the order card expect (`getOrder`), and it is added to the agent's tools.
FAIL if any of these is missing, if it adds a second Orders API client, if it moves only the new tool's token to another mechanism while `listOrders` keeps the old one, or if it changes files beyond the new tool, its test, the agent's tool list and a small addition to the existing client (e.g. exposing the HTTP status). Refactoring the order card, adding shared modules or a token store is beyond the ask.
