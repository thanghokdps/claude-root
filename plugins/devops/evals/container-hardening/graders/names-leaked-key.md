---
type: llm
---

The Dockerfile bakes a live-looking payments key into an image layer through `ENV`, so anyone who can pull the image can read it.

PASS if the reply names the baked-in key as a problem, says it is compromised and must be rotated (a layer keeps it even after removal), and says the key is supplied at runtime instead.
FAIL if the reply treats the key as just another style issue, never mentions rotating it, or keeps it in the image.
