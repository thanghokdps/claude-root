---
type: llm
focus:
  source: file
  path: src/agent/tools/get-order.ts
---

This is `src/agent/tools/get-order.ts` after the run. The repo already has an Orders API client (`ordersApi` in `./orders-client`), an order-code schema (`OrderCode` in `./order-schema`) and a `listOrders` tool that passes `config.configurable.token` to `ordersApi`. The user said none of this.

PASS if all hold:
- It calls the existing `ordersApi` for one order; this file has no `fetch`, HTTP library or client of its own.
- Its input is validated with the existing `OrderCode` (or the same pattern), not a bare string.
- The token comes from `config` the way `listOrders` takes it, never from a schema field the model fills.
- The tool is named `getOrder`, the name the ADR and the order card expect.
FAIL if the file is empty or missing (the tool was not written), or if any of these is missing.
