---
type: regex
target:
  source: file
  path: docs/adr/0001-agent-architecture.md
pattern: 'none built yet|cancelOrder \(?planned'
match: not_contains
---

agent-feature Step 8 updates an ADR line that still calls a built piece unbuilt; the scaffold marks cancelOrder "none built yet" (Writes/HITL) and "planned" (Agents, Problem table).
