---
model: opus
effort: high
name: grill
description: Relentless one-question-at-a-time interview that stress-tests a plan, design, or decision until every branch of the decision tree is resolved. Surfaces weak points in conversation instead of in the implementation.
# Human-facing only: `disable-model-invocation` turns off auto-invocation, so
# `when_to_use` here tells the reader when to reach for it, not the model when to fire it.
when_to_use: reach for this by hand after /brainstorming produces a design.md, or any time a plan needs hardening before implementation — say "grill" or "/grill"
disable-model-invocation: true
---

# Grill

Interview the user relentlessly about a plan, design, or decision until you reach **shared understanding**. Walk down every branch of the decision tree, resolving dependencies between decisions one at a time.

This skill is **hostile, not collaborative**. A weak answer gets pushed on, not accepted.

**Trigger:** explicit only. The user must say `grill` (or `/grill`).

---

## The one rule that makes this work

> **Facts you look up. Decisions you ask.**

If something can be answered by reading the filesystem, running a command, or checking a doc — **go find it**. Never spend a question on it.

If something is a judgement call the user owns — **put it to them and wait**.

Getting this backwards is the main failure mode: asking "what test framework does this project use?" burns the user's turn on something `cat package.json` answers.

---

## Process

### Step 1 — Load the target (silent)

Identify what is being grilled:

| Input | Where to look |
|-------|---------------|
| A file path | Read that file — grill its contents, not the path string |
| Explicit text in the invocation | Use it directly |
| "this plan" / "the design" | `specs/<slug>/design.md`, then `specs/<slug>/PLAN.md` |
| Nothing given | Most recently modified `specs/*/design.md` or `specs/*/PLAN.md` |
| Still nothing | Ask **one** question: "What am I grilling?" — then stop |

Read `.claude/docs/index.md` if it exists — architecture, conventions, and stack are facts, so they come from there rather than from a question.

Then explore the codebase for anything the target depends on. Read the files it names. Check whether the things it assumes exist actually exist.

**Completion criterion:** every file, module, and command the target names has been read or confirmed missing. Ask nothing yet; narrate nothing you read.

### Step 2 — Map the decision tree (silent)

Sort everything in the target into three buckets:

- **Locked** — already decided with a stated reason. These stay closed.
- **Open branches** — decisions the plan needs but has not made.
- **Unstated assumptions** — things the plan silently takes for granted. These are the dangerous ones.

Order the open branches by **uncertainty × blast radius**: the branch that most changes the shape of everything downstream goes first.

**Completion criterion:** every line of the target lands in exactly one bucket.

### Step 3 — Grill (one question per turn)

Ask **exactly one question**. Then stop and wait.

Every question follows this shape:

```
**Q<n> — <the one-line question>**

Why this matters: <what breaks or forks depending on the answer>

My recommendation: <your actual answer, with reasoning>
```

Always give your recommended answer. A question without a recommendation makes the user do all the work. The recommendation is what lets them just say "yes" and move on — or react against it, which is often faster than answering cold.

One question per turn. Three at once buys one real answer and two shrugs.

Cycle through these categories as the tree demands:

| Category | The question underneath it |
|----------|---------------------------|
| Scope | What is explicitly NOT in this? |
| Assumption | What must be true for this to work, that nobody has verified? |
| Dependency | What has to land first? What breaks if it doesn't? |
| Failure mode | What happens when this fails halfway? |
| Rejected alternatives | What was considered and dropped, and why? |
| Success criteria | How do we know it worked — what command proves it? |
| Reversibility | How do we undo this after it ships? |
| Ownership | Who runs it, who gets paged, who maintains it? |
| Data | What happens to existing rows/records/state? |
| Boundary | What's the behaviour at 0, at 1, at max, at concurrent? |

**Hard-gate sweep.** Before closing, confirm the target has been questioned against every gate it touches: `auth · authorization · data-loss/migration · audit/security · external provider · public contract · weakening validation · high-blast file`. A gate the plan touches but never mentions is an unstated assumption, and it forces the `high-risk` lane.

### Step 4 — Push back

When an answer is weak, push before moving on. Weak answers look like:

- "We'll handle that later" → **When? What blocks on it? Is it in the plan or not?**
- "It should be fine" → **What makes it fine? What would make it not fine?**
- "That's an edge case" → **How often? What's the impact when it hits?**
- "We'll just add a flag" → **Who flips it? What's the default? When does it get removed?**

Push once, hard. If the user holds their position, record it as a **decision with a stated risk** and move to the next branch. You are not here to win.

### Step 5 — Close

Stop when every open branch is resolved or explicitly deferred.

Output:

```markdown
## Grill summary — <target>

### Decisions made
| # | Decision | Rationale |
|---|----------|-----------|
| D1 | <what was chosen> | <why> |

### Assumptions now explicit
- <assumption> — verified: yes/no

### Deferred (with risk accepted)
| # | Question | Deferred because | Risk if wrong |
|---|----------|------------------|---------------|

### Still open — blocks implementation
- <anything unresolved that must not be built around>

### Recommended plan changes
- <concrete edit to design.md / PLAN.md>

### Lane impact
- <unchanged, or: hard gate <name> surfaced → lane forced to high-risk>
```

Then ask: **"Write these back into `specs/<slug>/`?"**

On a yes, and only on a yes:

| Section | Destination |
|---------|-------------|
| Decisions made | `design.md` (or `PLAN.md` if that was the target) |
| Assumptions now explicit | `design.md` → `## Open questions` for the unverified ones |
| Deferred (with risk accepted) | `SUMMARY.md` → `## Deviations` |
| Still open — blocks implementation | `ESCALATIONS.md`, one entry each, `decision: pending` |
| Lane impact | `SUMMARY.md` → Lane field |

`ESCALATIONS.md` defaults to deny-on-no-response, so anything written there blocks dispatch until a human resolves it. That is the point: an unresolved grill finding stops the build instead of being remembered.

Use the template shape:

```
E00<n>
- raised_by: grill
- date: <YYYY-MM-DD>
- trigger: hard-gate | low-confidence | ambiguous-direction
- question: <the unresolved question, one sentence>
- context: <what work is blocked on this>
- options:
    - A) <option + consequence>
    - B) <option + consequence>
- default_if_no_response: BLOCK
- decision: pending
```

A grill leaves nothing on disk unless asked.

---

## Hard gates

- **Stay in interview mode** — the grill produces questions, a summary, and (on request) spec edits. Implementation waits for the user to confirm shared understanding *and* explicitly ask you to build.
- **A plan that looks fine is a plan whose assumptions you have not found yet.** Run the full tree even when nothing looks wrong.
- **One question per turn**, every turn.
- **Locked decisions stay locked.** If the user already chose and gave a reason, it is closed.

---

## Where this sits in the chain

```
/brainstorming   → produces specs/<slug>/design.md
      ↓
/grill           → hardens it — this skill
      ↓
/writing-plans   → converts to PLAN.md
      ↓
/coordinator     → dispatches implementation
```

`/brainstorming` builds a design from a rough idea and is collaborative.
`/grill` attacks a design that already exists and is adversarial.
`/blast-radius` answers the same "what breaks?" question about a diff that already exists; `/grill` asks it about a plan that does not.

Grilling a fresh idea with nothing decided yet is the wrong tool — `/brainstorming` first.

---

## Quick reference

```
/grill                                  # grills the most recent design.md
/grill specs/dark-mode/design.md        # grills a specific file
/grill we're going to cache user perms in Redis with a 5min TTL
```
