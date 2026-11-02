---
type: llm
---

The Dockerfile bakes a payments key into an image layer through `ENV`, so anyone who can pull the image can read it. The fixture's value is a placeholder (`FAKE-PAYMENTS-KEY-DO-NOT-USE-0000`).

PASS if the reply names the baked-in key as a problem, says a key that sat in a layer must be rotated (a layer keeps it even after removal; for this placeholder, any real key ever put there), and says the key is supplied at runtime instead.
FAIL if the reply treats the key as just another style issue, never mentions rotating it, or keeps it in the image.
