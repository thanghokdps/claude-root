---
model: opus
effort: high
name: writing-skills
description: Reference for authoring and pruning skills in this harness.
# Human-facing only: this skill fires by hand when you are editing a SKILL.md, so it
# takes its own advice and pays zero context load. `when_to_use` tells the reader, not the model.
when_to_use: adding a skill to skills/, rewriting one that has grown stale, deciding whether a skill should be model-invoked, or working out why a skill keeps stopping early — say "/writing-skills"
disable-model-invocation: true
---

# Writing Skills

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same *process* every run, not producing the same output — is the root virtue. Every lever below serves it.

This repo is the source library. A skill written here propagates to `~/.claude/skills/` and to every project via `/project-init`, so a sloppy skill is a sloppy skill everywhere.

---

## Invocation — pick one, and pay its cost

| | Model-invoked | User-invoked |
|---|---|---|
| Mechanics | omit `disable-model-invocation` | `disable-model-invocation: true` |
| `description` is read by | the model, as trigger conditions | a human, as a one-line summary |
| Cost | **context load** — the description sits in the window every turn | **cognitive load** — *you* must remember it exists |
| Reachable by other skills | yes | no |

Choose model-invocation only when the agent must reach the skill on its own, or another skill must reach it. A skill that only ever fires by hand should be user-invoked and pay no context load — `/grill` is the example in this repo.

When user-invoked skills multiply past what you can remember, the cure is a **router skill** that names the others and when to reach for each. `/coordinator` is this harness's router.

---

## Frontmatter

| Field | Purpose |
|-------|---------|
| `name` | slash command — `/name`. Must match the directory name. |
| `description` | model-invoked: triggers. user-invoked: human summary. |
| `model` | `opus` across this harness — every skill runs on Opus 5 |
| `effort` | `high` / `medium` / `low` |
| `when_to_use` | phrase patterns that trigger auto-invocation |
| `disable-model-invocation` | `true` = user-invoked only |
| `background` | `true` = runs as a background agent |
| `isolation` | `worktree` = isolated git worktree for parallel runs |

### Writing the description

A model-invoked description does two jobs: state what the skill is, and list the **branches** that should trigger it. Every word costs context load, so it earns harder pruning than the body.

- **Front-load the leading word** — the description is where it does its invocation work.
- **One trigger per branch.** Synonyms renaming a single branch are duplication: "build features using TDD … asks for test-first development" is one branch written twice. Collapse them.
- **Cut identity already in the body.** Keep it to triggers, plus any "when another skill needs…" reach clause.

---

## Information hierarchy

A skill is built from **steps** (ordered actions) and **reference** (rules and definitions consulted on demand). They mix freely. The decision is where each sits on the ladder, ranked by how immediately the agent needs it:

1. **In-skill step** — an ordered action in `SKILL.md`. Each ends on a **completion criterion**: the condition telling the agent the work is done. Make it *checkable* (can the agent tell done from not-done?) and, where it matters, *exhaustive* ("every modified model accounted for", not "produce a change list"). A vague criterion invites premature completion.
2. **In-skill reference** — a rule or definition in `SKILL.md`. Often a legitimately flat peer-set — every rule on one rung is fine, not a smell.
3. **External reference** — pushed into a sibling file, reached by a **context pointer**, loaded only when the pointer fires.

**Progressive disclosure** is the move down that ladder so the top stays legible. A **branch** — a distinct way the skill gets used — is the cleanest test: inline what every branch needs, push behind a pointer what only some branches reach. The pointer's *wording*, not its target, decides how reliably the agent follows it.

**Co-location** decides what sits *beside* a thing once placed: keep a concept's definition, rules, and caveats under one heading rather than scattered.

---

## When to split

Each cut spends one of the two loads, so split only when the cut earns it.

- **By invocation** — split off a model-invoked skill when it has a distinct leading word that should trigger it alone, or another skill must reach it. You pay context load for the new always-loaded description.
- **By sequence** — split a run of steps when the steps still ahead tempt the agent to rush the one in front of it. Keeping them out of view buys more legwork on the current task. This harness already does this: `/brainstorming` → `/grill` → `/writing-plans` are three skills, not one.

---

## Leading words

A **leading word** is a compact concept already in the model's pretraining that the agent thinks *with* while running the skill — *tight*, *red*, *seam*, *tracer bullet*, *fog of war*. Repeated through the text, it accumulates a distributed definition and anchors a whole region of behaviour in very few tokens by recruiting priors the model already holds.

It serves predictability twice: in the body it anchors *execution*; in the description it anchors *invocation*, because the same word living in your prompts, docs, and code links them to the skill.

Hunt for restatements a leading word retires:

- "fast, deterministic, low-overhead" → **tight** (a *tight* loop)
- "a loop you believe in" → **red** (the loop goes *red* on the bug, or it doesn't)

You win twice: fewer tokens, and a sharper hook for the agent to hang its thinking on.

---

## Pruning

Keep each meaning in a **single source of truth** — one authoritative place, so changing the behaviour is a one-place edit. In this harness that often means pointing at `rules/*.md` instead of restating a rule inside a skill.

Check every line for **relevance**: does it still bear on what the skill does?

Then hunt **no-ops** sentence by sentence. Run the test on each sentence in isolation — does it change behaviour versus the default? — and when one fails, delete the whole sentence rather than trim words from it. Be aggressive; most prose that fails should go, not be rewritten.

---

## Failure modes

Use these to diagnose a skill that is misbehaving.

- **Premature completion** — a step ends before it is genuinely done, attention slipping to *being done*. Fix the completion criterion first (cheap, local). Only if it is irreducibly fuzzy *and* you observe the rush, hide the later steps by splitting.
- **Duplication** — the same meaning in two places. Costs maintenance and tokens, and inflates that meaning's apparent rank on the ladder.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
- **Sprawl** — simply too long, even when every line is live. The cure is the ladder: disclose reference behind pointers, split by branch or sequence.
- **No-op** — a line the model already obeys by default, so you pay load to say nothing. A weak leading word (*be thorough*, when the agent is already thorough-ish) is a no-op; the fix is a stronger word (*relentless*), not a different technique.
- **Negation** — steering by prohibition backfires: *don't think of an elephant* names the elephant. Prompt the **positive** — state the target behaviour so the banned one is never spoken. Keep a prohibition only as a hard guardrail you cannot phrase positively, and pair it with what to do instead.

---

## Shipping a skill in this repo

1. `skills/<name>/SKILL.md` with the frontmatter above.
2. Add the row to `skills/README.md` and place it in the right chain.
3. `cp -r skills/<name> ~/.claude/skills/` to install globally.
4. Add to the `for skill in …` loop in `scripts/init.sh` only if projects need their own copy — globally installed skills already reach every project.
5. Test the trigger: state the phrase from `when_to_use` and confirm it fires.
