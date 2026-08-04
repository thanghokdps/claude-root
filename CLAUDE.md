# Claude Harness — Skill Library

Portable skill/agent/hook/rule library. Distributed to `~/.claude/` and bootstrapped into each project via `/project-init`.

---

## Session Resume (read FIRST every session)

```bash
cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md
cat ~/.claude/docs/solutions/INDEX.md 2>/dev/null
```

---

## What this project is

A **source library** — not an app. Changes here propagate to `~/.claude/` (global) and to all projects via `/project-init`.

```
Downloads/Claude/
  skills/       ← skill source files (not the installed versions)
  agents/       ← agent role definitions
  rules/        ← universal rules
  hooks/        ← bash automation scripts
  templates/    ← SUMMARY, TEST_MATRIX, ESCALATIONS templates
  scripts/      ← install/bootstrap scripts
```

Installed location: `~/.claude/skills/`, `~/.claude/rules/`, `~/.claude/hooks/`

---

## How to add a new skill

```bash
mkdir -p skills/<name>
# Create skills/<name>/SKILL.md with frontmatter:
# ---
# name: <name>
# description: <trigger condition — what makes Claude invoke this>
# model: opus
# effort: high | medium | low
# when_to_use: <phrases that trigger this skill>
# ---
```

Then install globally:
```bash
cp -r skills/<name> ~/.claude/skills/
```

## How to add a new rule

```bash
# Create rules/<name>.md
# Install:
cp rules/<name>.md ~/.claude/rules/
```

## How to add a new hook

```bash
# Create hooks/<name>.sh
chmod +x hooks/<name>.sh
cp hooks/<name>.sh ~/.claude/hooks/
# Register in ~/.claude/settings.json
```

---

## Skill frontmatter fields

| Field | Purpose |
|-------|---------|
| `name` | Slash command name — `/name` |
| `description` | Trigger condition — what makes the model invoke this |
| `model` | `opus` — every skill in this harness runs on Opus 5 |
| `effort` | `high` / `medium` / `low` |
| `when_to_use` | Phrase patterns that trigger auto-invocation |
| `background` | `true` = run as background agent |
| `color` | Display color in task list (blue, green, orange, red) |
| `isolation` | `worktree` = isolated git worktree for parallel execution |

## Agent frontmatter fields

| Field | Purpose |
|-------|---------|
| `model` | `opus` — every agent in this harness runs on Opus 5 |
| `permissionMode` | `bypassPermissions` for automation |
| `maxTurns` | Max agentic turns |
| `background` | `true` = background dispatch |
| `color` | Visual identifier in task list |
| `effort` | Effort override |
| `isolation` | `worktree` for safe parallel |

---

## Key rules (for this project itself)

- Skills must have specific `description` and `when_to_use` — model uses these as trigger conditions
- Every skill must work as a standalone unit — no undeclared dependencies
- Hooks must exit 0 (allow) or 2 (block) — never exit 1
- Rules must be imperative ("do X", "never Y") — not descriptive
- Test any new hook locally before installing: `echo '{}' | ./hooks/myhook.sh`
