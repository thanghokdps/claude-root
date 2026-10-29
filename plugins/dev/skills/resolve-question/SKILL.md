---
model: opus
effort: medium
name: resolve-question
description: Resolves an open question before anyone guesses or asks the user — sorts it into a fact the repo can answer or a choice, answers a fact with a file:line citation opened this session, tiers each choice by impact, asks the user only the high-impact ones as options, and decides the low-impact ones itself with a decision note (why, how to revert). Use when a plan, ticket or subagent has an open question.
when_to_use: an open question in a ticket or plan, a subagent reports it is blocked on a question, "do we already have X", "which file handles Y", "should I ask the user", "decide the small stuff yourself", "only ask me the risky choices", before asking the user anything during /ticket or /feature
---

# resolve-question — Answer from the repo, ask only what is a high-impact choice

**Invoke:** `/resolve-question <question> [<question> …]`

Every question put to the user costs a round trip, and a guess costs a wrong build. Most questions in a ticket are facts the repo already answers; of the choices, only the ones that are costly to get wrong belong to the user. The rest the agent decides, and writes down why, so the user can overturn any of them later.

**Citation** = `file:line` plus the quoted text at that line, from a file opened in this session. A remembered file is not a citation: open it.

---

## Step 1 — Sort each question

- **Fact**: the repo, its docs or its git history can answer it (where X lives, whether Y exists, what a function returns, which version is pinned).
- **Choice**: only the user can decide it (scope, trade-off, naming, priority, anything the ticket leaves open).
- Mixed → split it: the fact part goes to Step 2, the choice part to Step 4.
- Unsure → it is a choice. Never call your own question a fact to avoid asking.

**Done when:** every question is labelled fact or choice.

## Step 2 — Cite

Search (`Grep`, `Glob`, `git log -S`) and open the file. Found → answer with the citation and go to Step 6. A fact about how a dependency behaves is answered from its installed source (`node_modules/`, site-packages) at the pinned version, or from the official doc page fetched now, not from memory.

**Done when:** each fact has a citation, or goes to Step 3.

## Step 3 — Scan (a fact not found in one search)

Dispatch 2 `Explore` agents in one message, `model: "haiku"` (`~/.claude/rules/model-cost.md`), each starting in a different area (for example: source code / tests and fixtures, or docs and ADRs / git history), each told to return a citation or "not found". Same prompt twice errs twice, so the starting areas must differ.

- An agent's citation is a candidate. Open the cited lines yourself; a citation that does not say what the agent claims is dropped.
- Both cite the same thing and the lines say it → answered.
- They disagree, or one says not found → open both citations yourself and pick the one the code actually runs; still unclear → it becomes a choice.
- Both not found → the repo does not decide it: it is a choice.

**Done when:** each fact is cited or turned into a choice.

## Step 4 — Tier each choice

- **ask** (the user decides) when any holds: it touches a hard gate (auth/authz, data migration or loss, security/audit, external provider, public contract, weakening validation); it is hard to undo after merge (stored data shape, published API, money, PII); it changes scope or an acceptance criterion; the user has stated a preference on it; or the options are close and nothing in the repo breaks the tie.
- **decide** (the agent decides) otherwise: reversible inside this change, internal, and a repo convention, rule or fact from Steps 2–3 points one way.
- Unsure → ask. In a ticket the tiers match concern severity: ask = `blocking`, decide = `decide`.

**Done when:** every choice is labelled ask or decide.

## Step 5 — Ask the ask-tier choices

One question per turn, as 2–4 options with the one you recommend first and why, plus what each option changes. Facts found in Steps 2–3 go in the context line, so the user is never asked something the repo answered.

A decide-tier choice is never asked: take the recommended option and record it in Step 6. In auto mode ("implement all, don't ask") an ask-tier choice also takes the recommended option and is recorded the same way; on a `Risk: high` ticket it is challenged first (`${CLAUDE_PLUGIN_ROOT}/references/auto-decisions.md`).

**Done when:** every ask-tier choice is answered by the user, or taken in auto mode.

## Step 6 — Record

One line per answer, where the next reader looks: the ticket's `spec.md` § Decisions for a ticket, the plan's § Decisions for `/feature`, else a **Decided for you** list at the end of the reply.

```markdown
- <YYYY-MM-DD> <question> → <answer> (user)
- <YYYY-MM-DD> <question> → <answer> (agent) · why: <the fact or rule it rests on, with its citation> · revert: <what to change to undo it>
```

A fact keeps its citation. An `(agent)` line without `why:` and `revert:` is not a decision: `ticket-gate.sh` blocks a ticket's code commit on it.

**Done when:** every question has an answer with a citation or a recorded decision.

---

## Rules

- Never answer a fact from memory: open the file.
- Never send a fact to the user; never decide an ask-tier choice yourself outside auto mode; never decide without a note.
- A subagent cannot ask the user: it reports `Blocked: <question>` and the main session runs this skill.
- The same question twice in one task → straight to the user; no second scan.
