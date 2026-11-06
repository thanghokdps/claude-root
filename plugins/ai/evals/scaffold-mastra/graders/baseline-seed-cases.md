---
type: regex
target:
  source: file
  path: apps/agent/evals/datasets/baseline.jsonl
pattern: '^\{.*\}\s*$'
flags: m
match: "count:12"
---

The skeleton seeds twelve baseline eval cases.
