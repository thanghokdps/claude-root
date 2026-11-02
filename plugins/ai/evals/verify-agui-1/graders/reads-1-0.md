---
type: llm
---

The stream breaks three AG-UI 1.0 rules.

PASS if the reply names the reasoning message and span opened but never closed before `RUN_FINISHED` as the cause of the failed run, and also names at least one of: the missing `protocolVersion` on `RUN_STARTED`, or the non-standard `orderStatus` field being stripped (extra data belongs in `metadata`).
FAIL if it calls the stream valid, or blames only the text events.
