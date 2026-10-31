---
type: llm
focus: trace
---

Judge the tests the run wrote, attempted or proposed for the client (an attempted Edit or Write to a test file counts even when the sandbox denied it).

PASS if tests run offline against a mock or stub of the Shipfast API (a fake transport, stubbed HTTP, or recorded responses) and cover success, a mapped error, a timeout, and a retried read that eventually gives up.
FAIL if tests call the real `api.shipfast.example` host, if there are no tests, or if the client is only exercised by a manual smoke call.
