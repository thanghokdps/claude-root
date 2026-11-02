---
type: regex
target:
  source: file
  path: .env.example
pattern: '^PII_REDACTION=off\s*$'
flags: m
---

PII redaction is off by default.
