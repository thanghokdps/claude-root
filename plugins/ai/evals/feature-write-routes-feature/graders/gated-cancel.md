---
type: llm
focus: trace
---

The ADR now allows cancelling pending orders behind a confirm card. The repo has an Orders API client, an order-code schema and read tools that forward the caller's token.

Judge the cancel the run wrote, or planned if it stopped for approval first.
PASS if all hold:
- The cancel goes through the existing `ordersApi` client and `OrderCode`, not a new HTTP client or schema.
- The run pauses before the cancel call and cancels only on the customer's approve; reject or no answer cancels nothing.
- "Not yet shipped" is checked against the order's status read from the API, not trusted from the model or the card.
- The confirm card shows the order read from the API, and the ADR's "none built yet" is updated or flagged once built.
FAIL if the cancel can run before the decision, the status check relies on the model, or a second client or schema is added.
