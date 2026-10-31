# Auto decisions — debate what you decide for the user

Once building starts (the first edit to a file that is not a plan or spec), the user is not asked again: they answered everything up front, and they review the decisions at the end and roll back what they disagree with. A choice that would have been an ask-tier question is settled by a debate between subagents instead, and recorded. The same holds in auto mode or "implement all, don't ask" from the start.

## What counts

A choice the user would have been asked as options in a normal run: a contract question, a slice decision (reuse / extend / new), a confirm mechanism, a data shape, a waiver, scope that grows past the plan. Formatting, naming and anything the repo's rules already decide do not count: take the rule and note it.

Not a choice: an action no rollback undoes (push, merge, deploy, delete data, force-push, a migration on a shared database). Those still wait for the user's yes.

## The debate

0. **Past lessons.** Read `.claude/docs/decisions.md` when it exists (`/retro` settles past decisions there; lead, if installed) and take at most 3 entries, newest first, about the same kind of choice or the same files. They go into every brief and weigh in the judgment like a cited fact: a pick that repeats a choice later reverted names what is different this time.
1. **Advocates.** One subagent per option (2–3 options), `model: "sonnet"`, all in one message. Brief: the criterion, every option, the facts already cited, the past lessons, and "argue that <option> is the best choice for this repo; cite file:line for every claim; name the strongest failure of each other option". Rotate the order the options are listed in, so no option is first in every brief.
2. **Rebuttal** (hard gate only, see 4). Continue each advocate (`SendMessage` to its agent id) with the other advocates' arguments: "answer the strongest point against <option> with file:line; concede what you cannot answer". An advocate whose option nobody attacked says so instead of inventing an attack to answer. A concession counts against its option.
3. **Judge.** You (the main session) open every cited line; a citation that does not say what the advocate claims is dropped. Pick the option whose surviving arguments rest on facts (a file, a rule, a criterion), not taste, sized by how clearly it wins.
   - Conflicting arguments are the input, never a reason by themselves to take the most cautious or smallest option.
   - Weigh each argument on its facts, never by which advocate answered first, last or at greatest length.
   - Still tied on facts → the option the repo's existing convention matches; still tied → the one cheaper to revert.
4. **Red team.** When the choice touches a hard gate (auth/authz, data migration, security/audit, external provider, public contract, weakening validation), one more subagent, `model: "opus"`, gets the pick and every argument and is told "find the case where this pick fails". Switch only when it names a fact the pick missed.
5. A switch after code exists is a deviation: record it in § Deviations too.

Cost: one sonnet call per option per choice; on a hard-gate choice, one more sonnet call per option for the rebuttal and one opus call. Never debate a decide-tier choice.

## Format

In `docs/tickets/<id>/plan.md` for a ticket, the plan's § Decisions for `/feature`, else the **Decided for you** list at the end of the reply:

```markdown
## Auto decisions
- Rename write path · options: user's click via PATCH /api/conversations/:id / agent write behind interrupt · chose the click because the route already checks the owner · challenged: interrupt gives an audit row → kept, the route logs the rename · revert: move the write behind the interrupt in tools/rename.ts
- none: every choice was the user's (answered in chat)
```

Each entry needs `challenged:` (the strongest argument against the pick, and why it did not win) and `revert:`, which names the files to change: `/retro` settles the decision by the later commits on those files. On a `Risk: high` ticket in auto mode the `auto-decisions` hook (dev) blocks the stop until the section is there.

The final report lists every entry under **Decided for you**, so the user reviews them in one place, with the labels exactly as above (`challenged:`, `revert:`), never paraphrased.
