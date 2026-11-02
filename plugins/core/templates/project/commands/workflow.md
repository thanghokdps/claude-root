---
description: Write and launch a dynamic workflow for large-scale tasks — codebase audits, multi-file migrations, adversarial cross-checking, deep research.
argument-hint: "<task description>"
---

# Dynamic Workflow Launcher

**Task:** $ARGUMENTS

---

## Decision — workflow or wave agents?

Before triggering a workflow, confirm the task warrants it:

| Workflow | Wave agents (in-context) |
|----------|--------------------------|
| 10+ files changed independently | < 8 files |
| Codebase-wide audit or migration | Changes in 1–2 modules |
| Adversarial cross-check of results | Single linear pipeline |
| Orchestration worth saving/rerunning | One-off in-session coordination |

If wave agents suffice → use `/coordinator` instead.

---

## Trigger

**Prompt keyword:**
```
ultracode: $ARGUMENTS
```

**Natural language** (also works):
> "Use a workflow to audit all endpoints for missing auth checks"
> "Run a workflow for this migration"

**Whole session:**
```
/effort ultracode
```

Claude Code highlights the `ultracode` keyword. Press `Option+W` (macOS) / `Alt+W` (Windows/Linux) to dismiss if triggered accidentally.

---

## Built-in workflows

| Command | What it does |
|---------|-------------|
| `/deep-research <question>` | Fan-out web searches → fetch & cross-check sources → adversarial vote on each claim → cited report |

---

## Monitor a running workflow

```
/workflows                    list all runs
↑ / ↓                         navigate phases and agents
Enter or →                    drill into phase → agent (see prompt, tool calls, result)
Esc                           back out one level
p                             pause / resume the run
x                             stop selected agent or whole workflow
r                             restart selected running agent
s                             save script as a reusable command
```

A one-line progress summary also appears in the task panel below the input box. Press `↓` to focus it, `Enter` to expand.

---

## Save for reuse

After a run completes:
1. Run `/workflows` → select the run → press `s`
2. Choose save location:
   - `.claude/workflows/` — shared with team (commit to git)
   - `~/.claude/workflows/` — personal, available in all projects
3. The workflow becomes `/<name>` in slash-command autocomplete

Saved workflows accept arguments via `args`:
```
> Run /my-workflow with targets src/routes, src/api
```

---

## Limits and cost

| Constraint | Value |
|-----------|-------|
| Concurrent agents | 16 max |
| Total agents per run | 1,000 max |
| Mid-run user input | Not supported — split sign-off into sequential workflows |
| Session scope | Resumable within same Claude Code session only |
| Token cost | Meaningfully higher than single-session work — test on a slice first |

To gauge cost before a large run: scope to one directory or a narrow question, then scale up.

---

## Disable workflows

```json
{ "disableWorkflows": true }
```

in `settings.json`, or `CLAUDE_CODE_DISABLE_WORKFLOWS=1` environment variable.

---

## Action for $ARGUMENTS

1. Evaluate: does this need a workflow or can in-context wave agents handle it?
2. If workflow: trigger with `ultracode: $ARGUMENTS`
3. Approve the plan (view raw script with `Ctrl+G` before confirming if unsure)
4. Monitor via `/workflows`
5. After run: save with `s` if this orchestration is reusable
