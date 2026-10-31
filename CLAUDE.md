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
  .claude-plugin/marketplace.json  ← lists the 15 plugins below
  plugins/<plugin>/                ← self-contained: .claude-plugin/plugin.json (+ dependencies), skills/, references/
    progress    hooks only: skill checklist on start, ✅ per checkpoint, 🏁/⏹ at the end (never blocks)
    core        verify-done btw compact compound sync-memory project-init docs-sync constraints + branch-guard, edit-guard, secret-guard, sensitive-path, compact-advisor, step-limit, repo-profile, learn-capture hooks (always on; repo-profile enables the role packs frontend, backend, mobile, devops, ai and the domain pack workplace per repo) — plus scripts/init.sh and
                everything it copies: templates/ memory/ rules/ (rules/*.md → ~/.claude/rules/; rules/stacks/ holds only typescript, javascript, jest) hooks/stacks/ → progress
    plan        breakdown kickoff brainstorming grill domain-model writing-plans codebase-design → progress
                breakdown: requirement → tasks with criteria + estimates → issues on GitHub/GitLab/Jira → /ticket each
    review      review-checklist review-diff blast-radius create-pr resolve-pr-feedback debt-ledger repo-audit → progress
    dev         coordinator feature ticket resolve-question fix-bug tdd checkpoint → core, plan, review, ship
                feature is the supervisor: one slice table, each slice dispatched to a role pack's <role>-engineer (sonnet)
                + ticket-ledger, ticket-gate, test-lock, weakened-check, auto-decisions, ask-once, plan-recall, plan-gate hooks (always on: a ticket's commit/PR waits for its plan's skills; no question to the user once the build has started; an active PLAN.md stays live)
    frontend    role pack: agents/frontend-engineer.md + ui-feature design-ui + rules/ (react, nextjs) + references/ → progress, dev
    backend     role pack: agents/backend-engineer.md + api-endpoint db-change api-client + rules/ (python, fastapi, prisma) → progress, dev
                a role pack = one agents/<role>-engineer.md, deliverable-named skills, on-demand rules, deps exactly [progress, dev],
                no hooks (gates live in core/dev/ship so they run before the pack is enabled); lint-kit checks the shape
    ship        finish-branch ci-triage release-checklist write-migration incident sync-remote → core
                + release-gate hook (repos with eas.json: production releases need an approved release/<version>)
                + infra-gate hook (repos with *.tf, k8s/, Chart.yaml: a production terraform/kubectl/helm apply is a person's)
    mobile      role pack: agents/mobile-engineer.md + mobile-feature + rules/ (react-native) → progress, dev
    devops      role pack: agents/devops-engineer.md + pipeline container infra-change + rules/ (ci, container, infra) → progress, dev
    ai          role pack: agents/ai-engineer.md + agent-* (the deliverable is an agent) + rules/ (mastra, langgraph…) → progress, dev
    workplace   domain pack (HR / workplace apps): workplace-review + references/    → progress
                a domain pack = a plugin folder + its detect condition in core's repo-profile.sh + install.sh's off list
    lead        retro diagnose-session writing-skills                                 → core
    guards      hooks/hooks.json + hook scripts (opt-in)                              → dev
    harness     bundle of the eight process plugins — never the packs (frontend, backend, mobile, devops, ai, workplace): a bundle
                dependency cannot be disabled, so it could not stay off at user scope
  global/CLAUDE.md    ← installed to ~/.claude/CLAUDE.md
  eval/triggers/      ← one routing case per skill
  scripts/            ← install.sh, check.sh, lint-kit.py, eval-triggers.py (kit tooling, not shipped)
```

Install / update: `bash scripts/install.sh` — needed for global/CLAUDE.md and rules/ changes, and whenever a plugin is added (installs each plugin explicitly).

Behaviour evals (real model, paid, not in check.sh): `bash scripts/eval-plugin.sh <plugin>` runs `plugins/<plugin>/evals/` — one routing case per demo prompt, graded by which skill fired (`tool_used: Skill`). Before a demo: add `--runs 3 --ablation with-without`.

Upstream freshness (network, warn-only, not in check.sh): `bash scripts/check-upstream.sh` prints the latest npm version of each package in `scripts/upstream.json` beside the "checked against … on <date>" of every reference citing it, and flags references older than 30 days. Run it before touching the `ai` plugin's vendor guidance; re-date a reference only after re-reading its vendor source.

Deploy the docs site to Vercel production (`deploy prod`, `release site`): `bash scripts/release-site.sh`, after the user confirms. Never `vercel --prod` — git auto-deploy is off (`vercel.json`) and releases go only through the Deploy Hook in `VERCEL_DEPLOY_HOOK_URL`; if the shell lacks it, run `source ~/.zshrc && bash scripts/release-site.sh`, and never write the URL into a file.

Versions: every plugin stays at `1.0.0` until the kit is published — never bump a `version` on a change. After merging, reinstall with `bash scripts/install.sh` (it uninstalls and reinstalls every plugin, since an unchanged version keeps the old cached copy).

Release (only once published): bump `version` in the changed plugins' `plugin.json` (a GitHub install compares versions on `/plugin update`), merge, then `claude plugin tag plugins/<plugin> --push` → tag `<plugin>--v<version>`.

---

## How to add a new skill

1. `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter `name` (= directory), `description` (what + "Use when …"), `when_to_use`, `model`, `effort`. Never start a YAML value with a quote or backtick.
2. `eval/triggers/<name>.json`: 3 prompts that must rank it top-3, 1–2 owned by a neighbour skill.
3. Name a skill of another plugin only if that plugin is a dependency in `plugin.json`; otherwise write "(<plugin>, if installed)". `${CLAUDE_PLUGIN_ROOT}` is the skill's own plugin — no paths into another plugin.
4. `bash scripts/check.sh` — lint (incl. the dependency check), trigger eval, `claude plugin validate` per plugin.

## How to add a rule

Always-loaded context is the budget: add `paths:` frontmatter unless the rule applies to every task. Process detail belongs in `references/`, read by the skill that needs it. Global rules live in `plugins/core/rules/` (then `bash scripts/install.sh`); agent rules in `plugins/ai/rules/`, read on demand by the agent skills.

## How to add a hook

`plugins/guards/hooks/<name>.sh` (executable, reads JSON on stdin, exits 0 or 2 — never 1), register it in `plugins/guards/hooks/hooks.json` with `"${CLAUDE_PLUGIN_ROOT}"/hooks/<name>.sh`, test with `echo '{}' | plugins/guards/hooks/<name>.sh`. Prefer `additionalContext` JSON over exit 2 for non-blocking hints.

---

## Skill frontmatter fields

| Field | Purpose |
|-------|---------|
| `name` | Slash command name — `/name` |
| `description` | Trigger condition — what makes the model invoke this |
| `model` | `opus` on skills that decide (plan, architecture, review, security, migration, root cause); omitted on light, mechanical skills so they run on the session's model. The work a skill dispatches follows `plugins/core/rules/model-cost.md` |
| `effort` | `high` / `medium` / `low` |
| `when_to_use` | Phrase patterns that trigger auto-invocation |
| `context` / `agent` / `background` | `context: fork` runs it in a subagent; `background: false` waits for the result |
| `allowed-tools` / `arguments` / `paths` | Pre-approved tools · named `$args` · globs gating auto-load |

Any other key is silently ignored by Claude Code (`color`, `isolation` belong to agents) — lint fails on it. Full list: `SKILL_FIELDS` in `scripts/lint-kit.py`.

## Agent frontmatter fields

| Field | Purpose |
|-------|---------|
| `model` | by role, per `plugins/core/rules/model-cost.md`: `opus` for architect and reviewer, `sonnet` for agents that write code |
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
