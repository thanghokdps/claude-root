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

A **source library** and the `harness` marketplace of role plugins (local directory marketplace, loaded in place — edits are live in new sessions; a GitHub install is copied to the plugin cache).

```
<repo>/
  .claude-plugin/marketplace.json  ← lists the 10 plugins below
  plugins/<plugin>/                ← self-contained: .claude-plugin/plugin.json (+ dependencies), skills/, references/
    progress    hooks only: skill checklist on start, ✅ per checkpoint, 🏁/⏹ at the end (never blocks)
    core        verify-done btw compact compound sync-memory project-init — plus scripts/init.sh and
                everything it copies: templates/ stacks/ memory/ rules/ (rules/*.md → ~/.claude/rules/) hooks/stacks/ → progress
    plan        kickoff brainstorming grill domain-model writing-plans codebase-design → progress
    review      review-checklist review-diff blast-radius create-pr                   → progress
    dev         coordinator feature fix-bug tdd checkpoint design-ui                  → core, plan, review
                api-endpoint db-change ui-feature api-client (BE · DB · FE · API integration)
    ship        finish-branch ci-triage release-checklist write-migration             → core
    agent       agent-* + rules/ the skills read on demand                            → progress, dev, ship
    lead        retro diagnose-session writing-skills                                 → core
    guards      hooks/hooks.json + hook scripts (opt-in)                              → dev
    harness     bundle, depends on all nine
  global/CLAUDE.md    ← installed to ~/.claude/CLAUDE.md
  eval/triggers/      ← one routing case per skill
  scripts/            ← install.sh, check.sh, lint-kit.py, eval-triggers.py (kit tooling, not shipped)
```

Install / update: `bash scripts/install.sh` — needed for global/CLAUDE.md and rules/ changes, and whenever a plugin is added (installs each plugin explicitly).

Behaviour evals (real model, paid, not in check.sh): `bash scripts/eval-plugin.sh <plugin>` runs `plugins/<plugin>/evals/` — one routing case per demo prompt, graded by which skill fired (`tool_used: Skill`). Before a demo: add `--runs 3 --ablation with-without`.

Release: bump `version` in the changed plugins' `plugin.json` (a GitHub install compares versions on `/plugin update`), merge, then `claude plugin tag plugins/<plugin> --push` → tag `<plugin>--v<version>`.

---

## How to add a new skill

1. `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter `name` (= directory), `description` (what + "Use when …"), `when_to_use`, `model`, `effort`. Never start a YAML value with a quote or backtick.
2. `eval/triggers/<name>.json`: 3 prompts that must rank it top-3, 1–2 owned by a neighbour skill.
3. Name a skill of another plugin only if that plugin is a dependency in `plugin.json`; otherwise write "(<plugin>, if installed)". `${CLAUDE_PLUGIN_ROOT}` is the skill's own plugin — no paths into another plugin.
4. `bash scripts/check.sh` — lint (incl. the dependency check), trigger eval, `claude plugin validate` per plugin.

## How to add a rule

Always-loaded context is the budget: add `paths:` frontmatter unless the rule applies to every task. Process detail belongs in `references/`, read by the skill that needs it. Global rules live in `plugins/core/rules/` (then `bash scripts/install.sh`); agent rules in `plugins/agent/rules/`, read on demand by the agent skills.

## How to add a hook

`plugins/guards/hooks/<name>.sh` (executable, reads JSON on stdin, exits 0 or 2 — never 1), register it in `plugins/guards/hooks/hooks.json` with `"${CLAUDE_PLUGIN_ROOT}"/hooks/<name>.sh`, test with `echo '{}' | plugins/guards/hooks/<name>.sh`. Prefer `additionalContext` JSON over exit 2 for non-blocking hints.

---

## Skill frontmatter fields

| Field | Purpose |
|-------|---------|
| `name` | Slash command name — `/name` |
| `description` | Trigger condition — what makes the model invoke this |
| `model` | `opus` — every skill in this harness runs on Opus 5 |
| `effort` | `high` / `medium` / `low` |
| `when_to_use` | Phrase patterns that trigger auto-invocation |
| `context` / `agent` / `background` | `context: fork` runs it in a subagent; `background: false` waits for the result |
| `allowed-tools` / `arguments` / `paths` | Pre-approved tools · named `$args` · globs gating auto-load |

Any other key is silently ignored by Claude Code (`color`, `isolation` belong to agents) — lint fails on it. Full list: `SKILL_FIELDS` in `scripts/lint-kit.py`.

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
- Test any new hook locally before installing: `echo '{}' | ./plugins/guards/hooks/myhook.sh`
