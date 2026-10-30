# Plan Format Rules

Standard format for `specs/<slug>/PLAN.md` files.

## When to Create a Plan

Create a PLAN.md when the task meets ANY of:
- Spans > 3 discrete implementation steps
- Affects more than 2 files
- Estimated duration > 30 minutes
- Touches multiple architectural layers

Tiny-lane tasks with ≤ 3 steps do not need a PLAN.md — a SUMMARY.md is sufficient.

## Required Structure

```markdown
# Plan — <feature-name>

**Goal:** <one sentence>
**Architecture:** <relevant layers>
**Tech stack:** <languages/frameworks>
**Status:** draft | active | paused | complete

## Non-goals

- <explicit out-of-scope items>

## Success criteria

- [ ] <measurable outcome>

## File map

| File | Action | Layer |
|------|--------|-------|
| path/to/file.py | create | service |

## Tasks

\`\`\`xml
<task id="1.1" wave="1" status="done">
  <files>path/to/file.py</files>
  <action>Imperative instruction — what to do</action>
  <verify>pytest tests/test_file.py -x -q</verify>
  <done>All tests in test_file.py pass with exit 0</done>
</task>

<task id="1.2" wave="1">
  <files>path/to/other.py</files>
  <action>Imperative instruction — what to do</action>
  <verify>pytest tests/test_other.py -x -q</verify>
  <done>All tests in test_other.py pass with exit 0</done>
</task>
\`\`\`

## Risks

- <risk> → <mitigation>

## Status log

- <date> draft created
```

## Task Field Rules

- `wave`: tasks with the same wave number run in parallel (no file overlap allowed)
- `files`: comma-separated, exact paths — no globs
- `action`: imperative verb, complete instruction, no pseudo-code
- `verify`: shell command that exits 0 on success, completes within 60 seconds
- `done`: measurable acceptance state — not "looks good", but "test X passes"
- `status="done"` on the `<task>` tag marks it finished (set it once `<verify>` passes); a task without it is open

## Status and the plan hooks

- `**Status:**` moves draft → active when the build starts, → complete when every task is done; `paused` sets a plan aside without finishing it.
- While a plan is `active`, two always-on `dev` hooks keep it live: `plan-recall.sh` (UserPromptSubmit) injects its path, first open task and last 3 Status log lines every turn, so `/clear` or a compaction never loses the slice; `plan-gate.sh` (Stop) blocks a turn from ending once while a task is open — finish it, mark it `status="done"`, or set `paused`.
- Append a line to `## Status log` whenever a task's status or the plan's Status changes.

## XML in Markdown

Always wrap `<task>` blocks in a fenced code block (` ```xml `) to prevent the markdown renderer from interpreting the tags.
