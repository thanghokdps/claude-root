---
model: opus
effort: high
name: brainstorming
description: Design-first brainstorming session before any implementation. Explores intent, proposes multiple approaches, asks clarifying questions one at a time, and produces a design doc (specs/<slug>/design.md) before handing off to /writing-plans.
---

# Brainstorming

You MUST complete this skill before any creative or non-trivial implementation work. Design first, code second — even "simple" things deserve a design phase.

---

## Process (complete all steps in order)

### Step 1 — Explore project context

Read relevant files to understand:
- Existing architecture and patterns
- Conventions used in similar features
- What already exists that could be reused

### Step 2 — Clarify intent (one question at a time)

Ask clarifying questions **one at a time**. Prefer multiple-choice. Do not ask the next question until the user answers the current one.

Stop asking when you have enough to propose concrete approaches.

### Step 3 — Propose multiple approaches

Present 2–3 distinct approaches with trade-offs:

```
Approach A — <name>
  Summary: <what it does>
  Pros: <advantages>
  Cons: <disadvantages>
  Best when: <conditions>
```

Ask the user to pick one or describe a hybrid.

### Step 4 — Design the chosen approach

Produce a design covering:
1. **System context** — what this interacts with, what it changes
2. **Interface** — inputs, outputs, public contracts
3. **Data model** — schemas, fields, relationships (if relevant)
4. **Error paths** — what can go wrong and how it's handled
5. **Dependencies** — external services, libraries, internal modules

Scale depth to complexity — brief for simple changes, detailed for multi-layer work.

### Step 5 — Review the design

Ask the user: "Does this design look right? Any changes?"

Iterate until approval. Then proceed.

### Step 6 — Write the design doc

Save to `specs/<slug>/design.md` where `<slug>` is a kebab-case name derived from the feature.

```markdown
# Design — <feature name>

## Context
<what this feature does and why>

## Approach
<the chosen approach and rationale>

## Interface
<inputs, outputs, contracts>

## Data model
<schemas, fields — omit if not applicable>

## Error paths
<failure modes and handling>

## Dependencies
<what this relies on>

## Open questions
<anything unresolved>
```

### Step 7 — Hand off

Say: "Design complete. Run `/writing-plans` to convert this into an implementation plan."

---

## Rules

- Do NOT write any implementation code during brainstorming
- Do NOT invoke any skill other than `/writing-plans` (after completion) or a research agent if needed
- One question per message — never bundle multiple questions
- Multiple-choice questions are preferred over open-ended
- Never skip design because something "seems simple"
