---
type: llm
---

`scripts/rotate_logs.py` gzips `*.log` files older than 7 days (deleting the original) and deletes `*.log.gz` archives older than 30 days, in a directory given as argument (default `logs`).

PASS if the reply summarizes that behaviour briefly, including both the 7-day compress step and the 30-day delete step.
FAIL if it omits the deletion of old archives, misstates the thresholds, or gives no summary.
