---
type: regex
target:
  source: file
  path: docs/design/ui-map.md
pattern: '^(?=[\s\S]*^\|[^\n]*\blibrary primitive\b)(?=[\s\S]*^\|[^\n]*\bdesign primitive\b)(?=[\s\S]*components/ui/)'
flags: mi
---

The map has a primitives table: rows classed as library and design primitives, built in `components/ui/` (agent-design-ui Step 3). A regex, since an LLM judge on the whole map split votes run to run.
