---
type: regex
target:
  source: file
  path: package.json
pattern: '"format":\s*"prettier --write'
---

Every skeleton step runs `pnpm format`, so the root needs the script beside `format:check`. A run without it left 41 unformatted files (#194).
