---
type: llm
---

Each tenant has its own documents, so the tenant filter is an authorisation boundary.

PASS if the reply says the tenant filter must be set on the server from trusted context (request context / verified identity), and must not be left to a filter the model can set. It may still use the stock query tool if it explains how the tenant scope is enforced server-side (an own createTool merging the filter, or a per-tenant store or namespace). It should also mention, or ask about, the ingest side: tenant metadata on every chunk.
FAIL if it wires createVectorQueryTool with a model-controlled filter as the only tenant isolation, or does not address tenant isolation at all.
