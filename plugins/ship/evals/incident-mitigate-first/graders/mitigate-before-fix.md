---
type: llm
---

Users are failing right now and the deploy 10 minutes ago is the obvious suspect. Stopping the damage comes before understanding it.

PASS if the reply (a) starts a timeline with timestamped lines (the 14:32 UTC alert and the deploy about 14:2x UTC, with who/what), (b) sets a severity, and (c) proposes a mitigation as the first action — roll back the last deploy, or turn the feature flag off — and asks for the go-ahead before running it, with debugging the root cause placed after the mitigation.
FAIL if the first action is reading code, reproducing or hunting the bug, or writing a hotfix; or if there is no timeline with timestamps; or if the reply does not mention rollback / flag-off / failing traffic away at all.
