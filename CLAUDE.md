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

A **source library** and the `thang-kit` Claude Code plugin (local marketplace, loaded in place — edits are live in new sessions).

```
Downloads/Claude/
  .claude-plugin/     ← plugin.json + marketplace.json
  skills/             ← plugin skills (invoked as /<name> or /thang-kit:<name>)
  hooks/              ← hook scripts + hooks/hooks.json (plugin-registered); hooks/stacks/ = per-project
  references/         ← process docs skills read on demand (${CLAUDE_PLUGIN_ROOT}/references/...)
  global/CLAUDE.md    ← installed to ~/.claude/CLAUDE.md
  rules/              ← installed to ~/.claude/rules/ — always loaded unless they have `paths:`
  stacks/             ← stack-specific rules/skills copied into projects by init.sh
  templates/          ← specs templates; templates/project/{agents,commands} for STANDALONE init
  eval/triggers/      ← one routing case per skill
  scripts/            ← install.sh, init.sh, check.sh, lint-kit.py, eval-triggers.py
```

Install / update: `bash scripts/install.sh` (only needed for global/CLAUDE.md and rules/ changes).

---

## How to add a new skill

1. `skills/<name>/SKILL.md` with frontmatter `name` (= directory), `description` (what + "Use when …"), `when_to_use`, `model`, `effort`. Never start a YAML value with a quote or backtick.
2. `eval/triggers/<name>.json`: 3 prompts that must rank it top-3, 1–2 owned by a neighbour skill.
3. `bash scripts/check.sh` — lint, trigger eval, `claude plugin validate`.

## How to add a rule

Always-loaded context is the budget: add `paths:` frontmatter unless the rule applies to every task. Process detail belongs in `references/`, read by the skill that needs it. Then `bash scripts/install.sh`.

## How to add a hook

`hooks/<name>.sh` (executable, reads JSON on stdin, exits 0 or 2 — never 1), register it in `hooks/hooks.json` with `"${CLAUDE_PLUGIN_ROOT}"/hooks/<name>.sh`, test with `echo '{}' | hooks/<name>.sh`. Prefer `additionalContext` JSON over exit 2 for non-blocking hints.

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
