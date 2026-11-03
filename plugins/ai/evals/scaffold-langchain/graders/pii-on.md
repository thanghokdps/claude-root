---
type: regex
target:
  source: file
  path: .env.example
pattern: '^PII_REDACTION="?on"?\s*$'
flags: m
---

PII redaction is on by default on LangChain: its detectors are regex, with no model call.
