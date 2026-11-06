---
type: regex
target:
  source: file
  path: .env.example
pattern: '^PII_REDACTION="?on"?\s*$'
flags: m
---

PII redaction is on by default on custom LangGraph: its detectors are regex, with no model call. This grader also fails when the run left no `.env.example`.
