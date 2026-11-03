---
type: regex
target:
  source: file
  path: evals/datasets/baseline.jsonl
pattern: '^\{.*\}\s*$'
flags: m
match: "count:12"
---

The baseline dataset has twelve seed cases, one JSON object per line.
