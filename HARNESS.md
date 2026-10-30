# HARNESS — the control layer

The skills answer *"how do I build this?"*. The harness answers *"how careful should I be, and who needs to approve?"*. This page is the control model: lanes, hard gates, what the hooks enforce, and what the session remembers. How the kit is packaged is in [`DESIGN.md`](DESIGN.md); the install and daily use in [`docs/USAGE.md`](docs/USAGE.md).

## The one principle

> **Ceremony scales with risk. Human interruption scales with ambiguity.**

- **Risk** decides how much proof and process a change gets (the lane).
- **Ambiguity** decides whether a person is asked, and only to confirm intent, never to classify risk.

High risk and unambiguous runs on its own through heavy proof. Low risk and ambiguous still pauses to ask.

## Lanes

The Auto-Coordinator in the global `CLAUDE.md` (full logic in `dev:coordinator`) classifies every request silently and shows `Intent · Lane · Routing` for anything above tiny.

| Lane | When | Ceremony |
|---|---|---|
| **tiny** | one file, reversible | just do it; the hooks are the safety net |
| **normal** | several files, internal | plan mode → approve → implement → `/verify-done` |
| **high-risk** | a hard gate is hit | `specs/<slug>/` with SUMMARY, PLAN, TEST_MATRIX and ESCALATIONS (or `docs/tickets/<id>/` for a ticket) → the user confirms → build → review including `/security-review` |

**Hard gates**, always high-risk and never self-downgraded: auth or authorisation, data migration, security or audit, external providers, public contracts, weakening validation, `.claude/` config. A hard gate discovered mid-task escalates the lane regardless of where it started. Stopping rules: three turns still broken → stop patching, name the assumption that may be wrong, ask one diagnostic question.

## What the hooks enforce

A skill's text is read once and forgotten under pressure, so what must happen is checked by a hook ([DDR 0005](docs/ddr/0005-hooks-enforce-the-process.md)). Hooks exit 0 (allow) or 2 (block), never 1; a hint that should not block uses `additionalContext` or a permission `ask`.

| Arrives with | Hook | Guarantees |
|---|---|---|
| every role (`core`) | `branch-guard` | no push to `main` or an environment branch; no force, delete or mirror push to a protected branch |
| | `secret-guard` | `.env*`, keys, keystores and service accounts are never read, printed, copied or edited |
| | `sensitive-path` | an edit to secrets, CI/deploy config or `.claude/settings*.json` asks a person first |
| | `edit-guard` | repo files change through Edit/Write, so the per-edit lint and format hooks always run |
| | `step-limit` | a subagent past 90 tool calls stops and reports, instead of looping |
| | `repo-profile`, `compact-advisor`, `learn-capture` | the session knows what the repo is; `/compact` is suggested when the context is large; lessons are captured and promoted without a model in the loop |
| developers (`dev`) | `ticket-ledger` + `ticket-gate` | a ticket's commit waits for the skills its `plan.md` names and for every blocking concern to have a decision; its PR waits for `/verify-done` and `/review-checklist` |
| | `test-lock` | the test that reproduces a bug stays as written while the fix is made |
| | `weakened-check` | a commit that lowers the bar (deleted test, loosened assertion or validation) asks first |
| | `auto-decisions` | on a high-risk ticket worked without the user, every choice Claude made alone is listed |
| release owners (`ship`) | `release-gate` | a production mobile release ships only the exact commit of an approved `release/<version>` PR/MR; Claude never approves its own |
| opt-in (`guards`) | `commit-quality-gate`, `risk-corroboration`, `push-evidence` | no secrets or debug artifacts in a commit; a diff that trips a hard gate cannot ship as a lower lane; no push without a check after the last change |
| | `scope-gate`, `blast-radius-check`, `format-on-edit` | risk flags on every prompt; edits outside the plan's file set are flagged; edited files are formatted |
| | `run-log`, `session-handoff`, `session-resume`, `state-breadcrumb`, `notify-on-finish` | the command log behind the PR's Witness line; a handoff written at the end and read at the start; a breadcrumb per session; a notification when a long turn ends |
| every role (`progress`) | `skill-progress` | a skill's checklist and live ✅ progress; never blocks |

Every gate has a written waiver (`skip /<skill>: <reason>` in `plan.md`), so a skipped step is a recorded decision. What a hook does not check is convention: commit message quality, branch naming, filling in `CLAUDE.md`, writing plan docs. **Rule:** what can be mechanised is a hook; convention is the residue.

## Evidence over claims

"Tests pass" in a PR is the model's words. The harness replaces claims with records ([DDR 0006](docs/ddr/0006-evidence-over-claims.md)):

- `/verify-done` re-runs the checks that prove the "done when" condition in the session and reports their output.
- `run-log` (guards) records every shell command; `/create-pr` fills the PR's **Witness** line from it and never by hand, and "not recorded" stays when there is no log.
- A PR's **Demonstration** shows Before and After produced the same way, with a one-line Delta.
- `/resolve-question` answers a fact only with a `file:line` citation opened in the session; only a real choice reaches the user, as options.
- `push-evidence` (guards) asks before a push when no check ran after the last change.

## Who does the work

Opus plans, decides and reviews. Code from an approved plan is written by Sonnet; mechanical work and searches go to Haiku. A subagent stuck twice on the same check goes back to Opus to re-plan, never a third try on the same brief. The brief to a cheaper model leaves nothing to decide: files, contract, the test to pass, the done check. The user naming a model overrides the table ([DDR 0003](docs/ddr/0003-model-by-role.md)).

## What the session remembers

```text
session start   specs/HANDOFF.md is read and deleted (CLAUDE.md "Session Resume", or guards' session-resume)
                repo-profile tells the session what the repo is; learn-promote lands queued lessons
during work     Claude saves feedback and decisions to the project memory the skills maintain
git commit      ticket-ledger records which skills ran on the branch (dev)
session end     /compact writes specs/HANDOFF.md and merges learnings
                /compound writes a lesson to docs/solutions/; learn-capture proposes lessons on its own
                guards: session-handoff, state-breadcrumb
team project    /sync-memory at the start of a session: pull, rebuild memory from your commits, flag overlaps
```

`.claude/docs/` (written by `/project-init`, kept current by `/docs-sync`) is what a new session reads instead of rescanning the code.

## Installing and updating

```bash
# Inside Claude Code: add the marketplace once (GitLab or the GitHub mirror, see the README), then
/plugin install dev@harness            # or harness@harness; role packs (frontend, backend, ai) turn on per repo
/plugin marketplace update harness     # later

# From a clone, which also installs the global CLAUDE.md and rules into ~/.claude/
bash <kit-dir>/scripts/install.sh

# Bootstrap a project, or refresh its .claude/ after kit changes
cd my-project && claude    # then /project-init
bash <kit-dir>/plugins/core/scripts/init.sh /path/to/project
```
