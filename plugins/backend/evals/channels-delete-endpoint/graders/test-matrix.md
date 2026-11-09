---
type: llm
focus:
  source: file
  path: apps/api/src/modules/channels/__tests__/channels.controller.test.ts
---

This is `apps/api/src/modules/channels/__tests__/channels.controller.test.ts` after the run, the Vitest route tests for the channels controller, run on a real Postgres through `app.inject`.

One check: a test in this file sends DELETE for a channel that belongs to a different workspace or user than the signed-in one, expects 404 (or 403), and afterwards asserts the channel still exists or is unchanged (a GET as the owner, a repository lookup, a row count — any proof the row survived).

PASS if such a test exists, whatever else the file covers.
FAIL if no delete tests were added, there is no test for another workspace's channel, or that test checks only the status code and never proves the row survived.
