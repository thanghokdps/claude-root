---
type: regex
target:
  source: file
  path: apps/agent/src/mastra/config/env.ts
pattern: 'DEV_USER_TIME_ZONE[\s\S]{0,120}resolvedOptions\(\)\.timeZone'
---

The dev user's zone defaults to the machine's. A `UTC` default answered "what is my local time?" seven hours off in Vietnam.
