---
type: llm
focus:
  source: file
  path: main.tf
---

This is `main.tf` after the run.

PASS if it declares an `aws_s3_bucket_lifecycle_configuration` for the exports bucket with a rule that expires objects after 30 days.
FAIL if there is no lifecycle configuration, the expiry is not 30 days, or the file is unchanged.
