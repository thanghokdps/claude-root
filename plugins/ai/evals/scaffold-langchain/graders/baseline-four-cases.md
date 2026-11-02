---
type: regex
target:
  source: file
  path: evals/datasets/baseline.jsonl
pattern: '^\{.*\}\s*$'
flags: m
match: 'count:4'
---

The baseline dataset has four seed cases, one JSON object per line.
