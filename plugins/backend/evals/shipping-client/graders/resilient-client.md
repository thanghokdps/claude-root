---
type: llm
focus: trace
---

Judge the client code the run wrote, attempted or proposed; an attempted Edit or Write counts even when the sandbox denied it.

PASS if the client (a) sets a timeout on every call, (b) reads the API key and base URL from environment or settings, never a literal, (c) retries with backoff only the idempotent reads (GET list and GET one, on 429/5xx or network errors) and does NOT retry `POST /shipments` unless it sends an idempotency key, (d) follows `next_cursor` pagination with a cap, and (e) maps upstream errors (404, 422) to the app's own error type.
FAIL if the key is hardcoded, if any call lacks a timeout, if the POST create is retried blindly, or if upstream payloads leak unmapped into callers.
