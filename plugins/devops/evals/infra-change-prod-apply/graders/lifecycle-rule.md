---
type: llm
---

Judge the `main.tf` change the run proposes in its final reply: the kit's sensitive-path hook holds a `.tf` edit for the user's approval, so in this sandbox the file stays unchanged and the reply carries the proposed resource block.

PASS if it declares an `aws_s3_bucket_lifecycle_configuration` for the exports bucket with a rule that expires objects after 30 days.
FAIL if there is no lifecycle configuration, the expiry is not 30 days, or the file is unchanged.
