---
model: opus
effort: high
name: domain-model
description: Builds and sharpens the project's ubiquitous language — challenges fuzzy terms, cross-checks vocabulary against the code, and records resolved terms in .claude/docs/glossary.md and hard-to-reverse decisions as ADRs. Use when terminology is drifting, when a design uses a word the codebase does not, or when a decision needs recording.
when_to_use: during /brainstorming or /grill when terms keep shifting meaning, before a design names new concepts, when two people mean different things by the same word, or when an architectural decision deserves a written rationale
---

# Domain Model

Sharpen the project's language *while* designing. This is the active discipline — challenging terms, inventing edge-case scenarios, writing the glossary down the moment a term crystallises.

Merely *reading* the glossary for vocabulary is not this skill; that is a habit any skill should have. This skill is for when you are **changing** the model.

---

## Where it lives

The harness keeps project knowledge in `.claude/docs/`. The domain model goes there too:

```
.claude/docs/
├── glossary.md          ← the ubiquitous language — terms only
└── adr/
    ├── 0001-<slug>.md   ← one decision per file, numbered, never renumbered
    └── 0002-<slug>.md
```

Create files lazily — only when there is something to write. No glossary yet? Create it when the first term resolves. No `adr/`? Create it when the first ADR earns its place.

`glossary.md` is a glossary and nothing else. Keep implementation detail, specs, and scratch notes out of it — those belong in `.claude/docs/architecture.md` or `specs/<slug>/design.md`.

---

## During the session

### Challenge against the glossary

When a term conflicts with what `glossary.md` already says, call it out the moment it happens:

> "The glossary defines *cancellation* as the whole order being voided, but you seem to mean a single line item — which is it?"

### Sharpen fuzzy language

When a term is vague or overloaded, propose a precise canonical one:

> "You're saying *account* — do you mean the Customer or the User? Those are different things, and the code already treats them differently."

### Stress-test with concrete scenarios

When domain relationships are under discussion, invent specific scenarios that probe the edges and force precision about where one concept ends and the next begins. Abstract agreement hides disagreement; a concrete scenario exposes it.

### Cross-reference with the code

When the user states how something works, check whether the code agrees. Contradictions are the highest-value finding this skill produces:

> "The code cancels whole Orders — `OrderService.cancel` has no line-item path — but you just said partial cancellation works today. Which is right?"

### Write terms down inline

When a term resolves, update `glossary.md` right then. Batching loses them.

```markdown
## <Term>

<One-sentence definition, in the project's own words.>

**Not:** <the neighbouring concept it gets confused with, and why it is different>
**In code:** <the type, table, or module where it lives>
```

---

## ADRs — offer sparingly

Offer an ADR only when **all three** are true:

1. **Hard to reverse** — changing your mind later carries meaningful cost.
2. **Surprising without context** — a future reader will ask "why did they do it this way?"
3. **A real trade-off** — genuine alternatives existed and one was picked for stated reasons.

Miss any one and skip the ADR. Most decisions do not need one; an `adr/` full of noise is worse than an empty one.

```markdown
# ADR <NNNN> — <title>

**Status:** accepted | superseded by ADR-<NNNN>
**Date:** <YYYY-MM-DD>

## Context
<the forces in play — what made this a real decision>

## Decision
<what was chosen>

## Alternatives considered
| Option | Why not |
|--------|---------|

## Consequences
<what this makes easy, what it makes hard, what it locks in>
```

Never renumber or delete an ADR. Supersede it with a new one and mark the old one's status.

---

## Where this sits in the chain

```
/brainstorming   → design.md
      ↕
/domain-model    → glossary.md + ADRs — this skill, running alongside
      ↕
/grill           → hardens the design
      ↓
/writing-plans   → PLAN.md
```

This skill runs **alongside** `/brainstorming` and `/grill` rather than after them. A design that names a concept the glossary has never heard of is exactly when to reach for it.

`/grill` asks whether a decision is right. `/domain-model` asks whether everyone means the same thing by the words in it.

---

## Hard gates

- **The glossary holds terms, not decisions.** Decisions go to ADRs; implementation goes to `architecture.md`.
- **Write it down when it resolves**, in the same turn.
- **A term the code contradicts is a finding**, not a detail — surface it before moving on.
- **An ADR needs all three tests.** Two out of three is a comment in the code.
