# Claude Code — Global Harness (harness)

Source of truth: the kit checkout (`claude plugin marketplace list` shows its path; marketplace `harness`: role plugins `<role>` under `plugins/` + `scripts/install.sh` for this file and `rules/`). Edit the kit, not `~/.claude`.

## Principles (every task)
1. **Ask once, up front** — state the interpretation, then before the first edit ask every open question, as many rounds as it takes (`AskUserQuestion`, up to 4 per call), until nothing is unclear. Once building starts, never ask: settle a new choice with `/resolve-question` (subagents debate the options, you judge), and end every build's report with a **Decided for you** list the user reviews or rolls back — every choice you made that the user did not, one line each, labels verbatim: `<choice> → <pick> · why: <fact, file:line> · challenged: <if debated> · revert: <what to change>` (`- none` when every choice was the user's). Still confirm actions no rollback undoes (push, merge, deploy, delete, force-push).
2. **Simplicity** — nothing beyond the ask; no single-use abstractions.
3. **Surgical** — every changed line traces to the request; note adjacent issues, don't fix them.
4. **Goal-driven** — define "done when <check>" first; test first where practical. Never claim done without fresh evidence.
5. **Communicate** — surface blockers immediately; explain a change of direction before making it. End a task's report with what you skipped or did not check, and any risk the user must know (one or two lines; omit when there is none).
6. **Terse but verbatim** — keep replies short, but quote code, errors, paths, commands and security warnings exactly, never paraphrased; point to evidence with `path:line` instead of pasting logs. First line is the answer or the next action, last line what comes next; cut openers that announce ("I'll…"), closers that ask "anything else?" and by-the-way sidebars, but keep a hedge that carries real uncertainty. Terseness yields when the user asks to explain or walk through (full length, with headings), when they ask for options (2–4 ranked, recommendation first), and before a destructive action (confirm first).
7. **Answer shape** — more than one step → numbered, fewest steps that work; work spanning turns → say where it stands ("step 3 of 5 done: …"). Show at most ~5 items per group, most relevant first (presentation only, never drop a relevant one). Estimates in units ("~15 min", "an afternoon"), never "a bit". Errors: cause and fix, no "uh oh". Three turns still broken → stop patching, name the assumption that may be wrong, ask one diagnostic question. Before sending: the first and last line alone must say what happened and what to do next.

## Auto-Coordinator
Action intent → classify lane silently (`/coordinator` holds the full logic):

| Lane | When | Ceremony |
|------|------|----------|
| tiny | 1 file, reversible | Just do it |
| normal | multi-file, internal | Built-in **plan mode** → approve → implement → verify |
| high-risk | hard gate hit | `specs/<slug>/` (SUMMARY, PLAN, TEST_MATRIX, ESCALATIONS), or `docs/tickets/<id>/` when working a ticket with `/ticket` → user confirms → build → review incl. `/security-review` |

Hard gates (always high-risk): auth/authz, data migration, security/audit, external providers, public contracts, weakening validation (`weakened-check` asks on commit), `.claude/` config.
Show `Intent · Lane · Routing` for normal/high-risk. Use a task list when the tool exists; never block on it.

## Daily loop
- Work arrives as a requirement → `/breakdown` (tasks with criteria and estimates on the tracker), then `/ticket <id>` per task; as a ticket id → `/ticket <id>` straight away.
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
- LLM-agent work (CopilotKit / LangGraph): in repos a team agent plugin covers (`space-agent:*`) that plugin wins; elsewhere → `/agent-*` (the `ai` pack).
- Impact of a code diff → `/blast-radius`; impact of a proposed change request → `business-analyst:analyze-impact`.
- Team-only skills (flash, BA/QA, `developers:verify-features`, `explain-code`, `develop-components`) have no kit equivalent — use them.

## Rules and references
- Always loaded: `~/.claude/rules/` `git` · `security` · `code-quality` · `model-cost`. Path-scoped: `typescript`, `testing`, `api-contract`, `app-structure`, `data-access`.
- On demand (skills read them): each plugin's `references/` — dev `orchestration` · `wave-parallelism` · `plan-format` · `auto-correct-scope` · `spec-templates` · `agent-prompts`; core `memory`.

## Gotchas
- `specs/` is gitignored. `settings.local.json` overrides `settings.json`.
- Personal playbook: `PLAYBOOK.md` in the kit checkout.
