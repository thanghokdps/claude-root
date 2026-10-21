---
model: opus
effort: low
name: init-project
description: Deprecated alias for /project-init.
when_to_use: kept so the old name still resolves — reach for /project-init instead
disable-model-invocation: true
---

# init-project — deprecated

The canonical bootstrap is **`/project-init`**. Run that.

It scans the project once and writes `.claude/docs/`, agents, hooks, rules, skills, commands, templates, memory, and `CLAUDE.md`.

---

## Why this is a stub

`/init-project` and `/project-init` were two full skills describing two *different* directory trees. `/init-project` created `.claude/commands/` and `.claude/docs/solutions/`; `/project-init` created `.claude/memory/*`. Neither created the other's directories, so whichever one you happened to run decided what your project got.

`/init-project` also hand-reimplemented what `scripts/init.sh` already does — copying agents, hooks, templates, writing `settings.json` — which is exactly the kind of duplicate list that drifts out of sync. Its Stage 6 then called `/project-init` anyway.

One path now: `/project-init` → `scripts/init.sh` (automation) → project scan (intelligence). The `.claude/commands/` copy that only lived here has moved into `init.sh`.
