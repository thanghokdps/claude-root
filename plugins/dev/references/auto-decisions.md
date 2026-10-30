# Auto decisions — debate what you decide for the user

Once building starts (the first edit to a file that is not a plan or spec), the user is not asked again: they answered everything up front, and they review the decisions at the end and roll back what they disagree with. A choice that would have been an ask-tier question is settled by a debate between subagents instead, and recorded. The same holds in auto mode or "implement all, don't ask" from the start.

## What counts

A choice the user would have been asked as options in a normal run: a contract question, a slice decision (reuse / extend / new), a confirm mechanism, a data shape, a waiver, scope that grows past the plan. Formatting, naming and anything the repo's rules already decide do not count: take the rule and note it.

Not a choice: an action no rollback undoes (push, merge, deploy, delete data, force-push, a migration on a shared database). Those still wait for the user's yes.

## The debate

1. **Advocates.** One subagent per option (2–3 options), `model: "sonnet"`, all in one message. Brief: the criterion, every option, the facts already cited, and "argue that <option> is the best choice for this repo; cite file:line for every claim; name the strongest failure of each other option".
2. **Judge.** You (the main session) open every cited line; a citation that does not say what the advocate claims is dropped. Pick the option whose surviving arguments rest on facts (a file, a rule, a criterion), not taste.
3. **Red team.** When the choice touches a hard gate (auth/authz, data migration, security/audit, external provider, public contract, weakening validation), one more subagent, `model: "opus"`, gets the pick and every argument and is told "find the case where this pick fails". Switch only when it names a fact the pick missed.
4. A switch after code exists is a deviation: record it in § Deviations too.

Cost: one sonnet call per option per choice, plus one opus call on a hard-gate choice. Never debate a decide-tier choice.

## Format

In `docs/tickets/<id>/plan.md` for a ticket, the plan's § Decisions for `/feature`, else the **Decided for you** list at the end of the reply:

```markdown
## Auto decisions
- Rename write path · options: user's click via PATCH /api/conversations/:id / agent write behind interrupt · chose the click because the route already checks the owner · challenged: interrupt gives an audit row → kept, the route logs the rename · revert: move the write behind the interrupt in tools/rename.ts
- none: every choice was the user's (answered in chat)
```

Each entry needs `challenged:` (the strongest argument against the pick, and why it did not win) and `revert:`. On a `Risk: high` ticket in auto mode the `auto-decisions` hook (dev) blocks the stop until the section is there.

The final report lists every entry under **Decided for you**, so the user reviews them in one place.
