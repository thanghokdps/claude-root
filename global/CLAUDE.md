# Claude Code — Global Harness (harness)

Source of truth: the kit checkout (`claude plugin marketplace list` shows its path; marketplace `harness`: role plugins `<role>` under `plugins/` + `scripts/install.sh` for this file and `rules/`). Edit the kit, not `~/.claude`.

## Principles (every task)
1. **Think first** — state the interpretation; one clarifying question beats a wrong build.
2. **Simplicity** — nothing beyond the ask; no single-use abstractions.
3. **Surgical** — every changed line traces to the request; note adjacent issues, don't fix them.
4. **Goal-driven** — define "done when <check>" first; test first where practical. Never claim done without fresh evidence.
5. **Communicate** — surface blockers immediately; explain a change of direction before making it.
6. **Terse but verbatim** — keep replies short, but quote code, errors, paths, commands and security warnings exactly, never paraphrased; point to evidence with `path:line` instead of pasting logs.

## Auto-Coordinator
Action intent → classify lane silently (`/coordinator` holds the full logic):

| Lane | When | Ceremony |
|------|------|----------|
| tiny | 1 file, reversible | Just do it |
| normal | multi-file, internal | Built-in **plan mode** → approve → implement → verify |
| high-risk | hard gate hit | `specs/<slug>/` (SUMMARY, PLAN, TEST_MATRIX, ESCALATIONS), or `docs/tickets/<id>/` when working a ticket with `/ticket` → user confirms → build → review incl. `/security-review` |

Hard gates (always high-risk): auth/authz, data migration, security/audit, external providers, public contracts, weakening validation, `.claude/` config.
Show `Intent · Lane · Routing` for normal/high-risk. Use a task list when the tool exists; never block on it.

## Daily loop
- One topic per session; resume instead of re-explaining. Bad edit → `Esc Esc` to rewind.
- Parallel tickets → separate sessions in git worktrees, not one session juggling both.
- Deep reasoning only where it pays: `ultrathink` in one prompt, `/effort` for the session. `ultracode` = dynamic workflow (fan-out), not deeper thinking.
- Every changed implementation file ships with its test, at the repo's test location (existing convention wins; no tests yet → ask: `__tests__/` beside the code or a separate `tests/` folder). Gates in order: typecheck → lint → tests.
- Before saying done: `/verify-done`. Review: `/review-checklist` → `/code-review` → `/code-review ultra` for auth/data branches; `/security-review` for security-sensitive code.
- Branch finished → `/finish-branch`. Watch PR/CI: `/loop 15m <task>`; red build → `/ci-triage`.
- Verify the running app, not just the code: Playwright MCP / Claude in Chrome / iOS Simulator.

## Overlap with team plugins (granbull)
Chosen per pair on content, not by plugin. When both are available:
- Debugging → `dev:fix-bug` (not `developers:fix-bug`). Review → `/review-checklist` (not `developers:review-changes`).
- Commit + push + open MR/PR → `developers:create-mr` (project conventions); `create-pr` only drafts description text.
- LLM-agent work (CopilotKit / LangGraph): in repos a team agent plugin covers (`space-agent:*`) that plugin wins; elsewhere → `/agent-*`.
- Impact of a code diff → `/blast-radius`; impact of a proposed change request → `business-analyst:analyze-impact`.
- Team-only skills (flash, BA/QA, `developers:verify-features`, `explain-code`, `develop-components`) have no kit equivalent — use them.

## Rules and references
- Always loaded: `~/.claude/rules/` `git` · `security` · `code-quality`. Path-scoped: `typescript`, `testing`.
- On demand (skills read them): each plugin's `references/` — dev `orchestration` · `wave-parallelism` · `plan-format` · `auto-correct-scope` · `spec-templates` · `agent-prompts`; core `memory`.

## Gotchas
- `specs/` is gitignored. `settings.local.json` overrides `settings.json`.
- Personal playbook: `PLAYBOOK.md` in the kit checkout.
