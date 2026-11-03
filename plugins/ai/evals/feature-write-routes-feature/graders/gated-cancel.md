---
type: llm
focus:
  source: file
  path: src/agent/tools/cancel-order.ts
---

Judge the cancel tool in src/agent/tools/cancel-order.ts. The repo already has `ordersApi` (orders-client.ts) and `OrderCode` (order-schema.ts); the read tools forward the caller's token from the tool config.

PASS if all hold:

- Every Orders API call goes through `ordersApi` and the order code is validated with `OrderCode`; the file has no `fetch`, HTTP client or order-code regex of its own.
- The order is read from the API with the caller's token, and "not yet shipped" is decided from that response's status, not from the tool's arguments.
- The run pauses (an interrupt or the repo's confirm gate) before the cancel call, and the confirm payload shows the order read from the API.
- The cancel call runs only on the customer's approve; reject, no answer or an expired confirm cancels nothing.
  FAIL if the cancel can run before the decision, the status comes from the model, or a second client or schema is added.
