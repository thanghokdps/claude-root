---
model: opus
effort: medium
name: resolve-question
description: Resolves an open question before anyone guesses or asks the user — sorts it into a fact the repo can answer or a choice only the user can make, answers a fact with a file:line citation opened this session, and asks the user only the choices, as options. Use when a plan, ticket or subagent has an open question.
when_to_use: an open question in a ticket or plan, a subagent reports it is blocked on a question, "do we already have X", "which file handles Y", "should I ask the user", before asking the user anything during /ticket or /feature
---

# resolve-question — Answer from the repo, ask only what is a choice

**Invoke:** `/resolve-question <question> [<question> …]`

Every question put to the user costs a round trip, and a guess costs a wrong build. Most questions in a ticket are facts the repo already answers; only a choice belongs to the user.

**Citation** = `file:line` plus the quoted text at that line, from a file opened in this session. A remembered file is not a citation: open it.

---

## Step 1 — Sort each question

- **Fact**: the repo, its docs or its git history can answer it (where X lives, whether Y exists, what a function returns, which version is pinned).
- **Choice**: only the user can decide it (scope, trade-off, naming, priority, anything the ticket leaves open).
- Mixed → split it: the fact part goes to Step 2, the choice part to Step 4.
- Unsure → it is a choice. Never call your own question a fact to avoid asking.

**Done when:** every question is labelled fact or choice.

## Step 2 — Cite

Search (`Grep`, `Glob`, `git log -S`) and open the file. Found → answer with the citation and go to Step 5.

**Done when:** each fact has a citation, or goes to Step 3.

## Step 3 — Scan (a fact not found in one search)

Dispatch 2 `Explore` agents in one message, `model: "haiku"` (`~/.claude/rules/model-cost.md`), each starting in a different area (for example: source code / tests and fixtures, or docs and ADRs / git history), each told to return a citation or "not found". Same prompt twice errs twice, so the starting areas must differ.

- Both cite the same thing → answered.
- They disagree, or one says not found → open both citations yourself and pick the one the code actually runs; still unclear → it becomes a choice.
- Both not found → the repo does not decide it: it is a choice.

**Done when:** each fact is cited or turned into a choice.

## Step 4 — Ask the choices

One question per turn, as 2–4 options with the one you recommend first and why, plus what each option changes. Facts found in Steps 2–3 go in the context line, so the user is never asked something the repo answered.

**Done when:** every choice is answered by the user.

## Step 5 — Record

Write each answer where the next reader looks: the ticket's `spec.md` or `plan.md` (§ Decisions) for a ticket, the plan for `/feature`, else the reply. A fact keeps its citation; a choice records who chose and the date.

**Done when:** every question has an answer with a citation or a recorded choice.

---

## Rules

- Never answer a fact from memory: open the file.
- Never send a fact to the user; never resolve a choice yourself.
- A subagent cannot ask the user: it reports `Blocked: <question>` and the main session runs this skill.
- The same question twice in one task → straight to the user; no second scan.
