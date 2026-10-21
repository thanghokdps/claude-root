---
paths:
  - "**/*prompt*.{ts,mts,md}"
  - "**/prompts/**"
  - "**/*{instruction,description,scope,boundar}*.{ts,mts}"
---

# Agent prompts, tool descriptions and scope rules

- Write in short bullets. One rule per bullet; no narrative.
- Keep the user's wording verbatim when they supply a rule or a phrase — edit around it, never paraphrase it.
- Describe only capabilities that exist as tools today. A prompt or suggestion that promises a missing feature is a defect.
- Every scope has an explicit "not mine" list and what to do instead (hand off, decline in one short line).
- Ambiguity is a defect: when two readings exist, the prompt says which wins or tells the agent to ask.
- Derive lists (tool names, scopes, capabilities) from the constants that define them; never hand-copy them into prose.
- No real people's names or real customer data in prompts or examples.
- Static instructions first, dynamic context (date, user, memory) last — keeps the prefix cacheable.
- Tests and evals assert on outcomes (tool chosen, data written, refusal given), never on exact wording.
