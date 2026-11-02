---
type: llm
---

PASS if the reply explains that Array.prototype.sort sorts in place and mutates the original array, and suggests a copy first (`[...nums].sort()`, `nums.slice().sort()`, `toSorted()`).
FAIL if it does not explain the in-place mutation or gives an unrelated answer.
