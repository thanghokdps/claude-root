# Auto decisions — challenge what you decided for the user

In auto mode or "implement all, don't ask", Claude takes its own recommended option. On a `Risk: high` ticket that choice is argued against before it stands, and the record goes in `docs/tickets/<id>/plan.md`. The `auto-decisions` hook (dev) blocks the stop until it is there.

## What counts

A choice the user would have been asked as options in a normal run: a contract question, a slice decision (reuse / extend / new), a confirm mechanism, a data shape, a waiver. Formatting, naming and anything the repo's rules already decide do not count.

## The challenge

1. For each rejected option, one subagent with `model: "haiku"` and the brief: the ticket's criterion, the options, the chosen one, and "argue that <rejected option> is the better choice for this repo; cite files". Run them in one message.
2. Read the arguments. Keep the choice, or switch when an argument names a fact the choice missed (a file, a rule, a criterion).
3. A switch after code exists is a deviation: record it in § Deviations too.

Cost: one haiku call per rejected option, only on high-risk tickets.

## Format

```markdown
## Auto decisions
- Rename write path · options: user's click via PATCH /api/conversations/:id / agent write behind interrupt · chose the click because the route already checks the owner · challenged: interrupt gives an audit row → kept, the route logs the rename
- none: every choice was the user's (answered in chat)
```

Each entry needs `challenged:`; the hook checks for it.
