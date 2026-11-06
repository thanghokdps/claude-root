---
type: regex
target:
  source: file
  path: .env.example
pattern: '^PII_REDACTION="?off"?\s*$'
flags: m
---

PII redaction is off by default on Mastra: its detector is a model call. This grader also fails when the run left no `.env.example`.
