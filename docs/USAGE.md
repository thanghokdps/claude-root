# Claude Harness — Usage Guide

From the first install to daily work, with the detail the [README](../README.md) leaves out. What the kit is and why: [`DESIGN.md`](../DESIGN.md). The control model: [`HARNESS.md`](../HARNESS.md).

1. [Prerequisites](#1-prerequisites)
2. [Install the plugins](#2-install-the-plugins)
3. [Install the global rules (optional)](#3-install-the-global-rules-optional)
4. [Bootstrap a project](#4-bootstrap-a-project)
5. [First session](#5-first-session)
6. [Daily workflow](#6-daily-workflow)
7. [Common tasks](#7-common-tasks)
8. [Team workflow](#8-team-workflow)
9. [Ending a session](#9-ending-a-session)
10. [Updating](#10-updating)
11. [Troubleshooting](#11-troubleshooting)
12. [Cheat sheet](#12-cheat-sheet)

## 1. Prerequisites

| Item | Requirement |
|---|---|
| Claude Code | CLI or desktop app |
| Git | `git --version` works |
| `jq` and `python3` | used by the hooks (`brew install jq`); without `python3` the progress hooks stay silent |
| Python 3.12 | only for headroom (optional context compression) |
| Node, Python, … | whatever your project needs |

## 2. Install the plugins

Inside Claude Code, add the marketplace from **one** source. Both hold the same commit:

| Source | Use it when | Command |
|---|---|---|
| GitLab (team) | on the company network or VPN, with Reporter access to `thang.hoquang/claude-kit` and an SSH key on GitLab | `/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git` |
| GitHub (mirror) | outside the VPN, or without GitLab access | `/plugin marketplace add thanghokdps/claude-root` |

Then install one role and reload:

```text
/plugin install dev@harness          # developer (brings core, plan, review, progress)
/plugin install agent@harness        # AI-assistant builder (brings dev, ship and their dependencies)
/plugin install harness@harness      # all eight general role plugins
/reload-plugins
```

Check with `claude plugin list` that the role and its dependencies are `✔ enabled`. For `agent` that is seven plugins: `progress core plan review ship dev agent`. If one is missing or disabled (an older install, or a plugin turned off at another scope), pin the set in the project's `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "progress@harness": true,
    "core@harness": true,
    "plan@harness": true,
    "review@harness": true,
    "ship@harness": true,
    "dev@harness": true,
    "agent@harness": true
  }
}
```

**MCP servers** the skills use when present (`claude mcp list`): Playwright (`claude mcp add playwright -- npx -y @playwright/mcp@latest`) so `/design-ui`, `/ui-feature` and `/agent-frontend` can check the page in a real browser at desktop and narrow widths; Figma only for `/design-ui` and `/agent-design-ui` from a Figma link.

**Domain plugins.** `agent` and `workplace` are not in the `harness` bundle. Installed by `scripts/install.sh` they stay off at user scope, and core's `repo-profile` hook enables one in a repo that needs it (an AI-assistant repo, or a `Domain: workplace` line in the project docs) by writing `.claude/settings.local.json`, effective next session. Installing `agent@harness` by hand enables it everywhere, which is fine on a machine used only for assistants.

## 3. Install the global rules (optional)

The plugins work on their own. The always-loaded `~/.claude/CLAUDE.md` (principles, lanes, the daily loop) and `~/.claude/rules/` (git, security, code quality, model cost; typescript, testing and the fullstack rules by path) come only from a clone:

```bash
git clone git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git <kit-dir>   # or git@github.com:thanghokdps/claude-root.git
bash <kit-dir>/scripts/install.sh
```

The installer is idempotent and takes no arguments. It backs up `~/.claude/CLAUDE.md`, `rules/` and `settings.json` to `~/.claude/backups/harness-install-<timestamp>/`, copies `global/CLAUDE.md` and `plugins/core/rules/*.md` into `~/.claude/`, registers the clone as the local marketplace `harness` unless one is already registered from GitLab or GitHub (that one is kept), installs every plugin, and migrates an old copy-based install. No `.env` is needed; `.env.sample` lists the optional variables (eval judge, model keys and tracing for agent projects, Figma).

**Headroom** (optional) compresses large tool output: `bash <kit-dir>/scripts/setup-headroom.sh`, needs Python 3.12. The `headroom-compress` hook (guards) then hints at it when output passes 8 KB.

## 4. Bootstrap a project

`/project-init` reads manifests and code and writes a `.claude/` workspace plus a project `CLAUDE.md` with real paths and commands. Run it once per project, and again after a big architecture change. In an empty folder there is nothing to read, so start from the row that matches:

| Your folder | Do this |
|---|---|
| Existing repo with code | `cd my-project && claude`, then `/project-init` |
| Empty folder, regular app | `git init`, then `/kickoff` with the documents you have (or `/brainstorming <idea>` when the approach is open) → `/writing-plans` → build wave 1 (the scaffold: manifest, test runner, lint, `.gitignore`, `.env.example`) → commit → `/project-init` |
| Empty folder, AI assistant | `git init`, then describe the assistant in plain words, for example *"a chatbot that helps customers track and change their orders"*. `/agent-architect` interviews, writes the ADR, scaffolds and runs `/project-init` itself. For an empty skeleton on a named stack say *init* and the stack: *"init chatbot với Next.js + CopilotKit + LangGraph"* |

From a shell instead of Claude Code:

```bash
bash <kit-dir>/plugins/core/scripts/init.sh [project-dir]                 # lean: skills, rules and hooks come from the installed plugins
STANDALONE=1 bash <kit-dir>/plugins/core/scripts/init.sh [project-dir]    # also copies rules, skills, commands, agents and hooks into .claude/
```

Standalone is for a repo shared with people who do not have the plugins. It also copies the project commands (`/task`, `/auto`, `/workflow`), the project agents, and the stack bundle that matches (`react-native`: `/verify-feature`, `/gen-tests`, `/figma-to-screen`; `nextjs`; `python`). Stack signals it detects: `tsconfig.json` or `typescript` (TypeScript), `react`, `jest`, `next` (Next.js), `requirements.txt` or `pyproject.toml` (Python), `fastapi`, `langgraph`.

What you get:

```text
your-project/
├── CLAUDE.md                  ← generated: Auto-Coordinator, session resume, key directories, commands, stack rules
└── .claude/
    ├── settings.json          ← hooks registered
    ├── docs/                  ← knowledge base: index, architecture, conventions, stack, entry points, test strategy
    ├── rules/                 ← project and stack rules
    ├── skills/ hooks/         ← only in standalone mode
    └── memory/
        ├── MEMORY.md          ← index, loaded every session
        ├── user.md            ← your role and preferences (gitignored: it carries your git name and email)
        └── project/context.md ← goals, active decisions, constraints, team
```

Then fill in three things once: scan the generated `CLAUDE.md` (Key Rules and Common Commands), write `memory/user.md` (role, preferences such as "TypeScript strict, never `any`"), and `memory/project/context.md` (goals with dates, decisions with why and how to apply, constraints, who is who).

## 5. First session

```bash
cd my-project && claude
```

- **Context loaded?** Ask *"what project are you working on?"*; the answer should name the stack and constraints from `CLAUDE.md` and `MEMORY.md`.
- **Hooks working?** Try `git push origin main` from the session: `branch-guard` blocks it with the reason. Ask Claude to read `.env`: `secret-guard` refuses and asks you for the value.
- **First push of `main`** to a new, empty remote is yours. Claude does not push to `main`; `/finish-branch` prints `git push -u origin main` for you to run, after which branches and PRs work as usual.
- **CI secrets** (for example an evals job): `gh secret set <NAME> --repo <owner>/<repo>` before the first PR that needs them. `/finish-branch` names any the workflows read that the repo lacks.
- **Remote Control** (driving Claude from claude.ai or your phone): questions arrive as plain text, since the option picker is not shown there, and Claude cannot open a new desktop session for you.

## 6. Daily workflow

Start: `claude` in the project. If the last session ended with `/compact`, `specs/HANDOFF.md` is read and Claude knows where to continue. On a team project, `/sync-memory` first.

Work: describe what you want. The Auto-Coordinator classifies it (tiny, normal, high-risk), routes it to the skill, and for anything above tiny shows `Intent · Lane · Routing` and a task list. A vague request gets questions first, one per turn with a recommendation, never a guessed build. The slash commands below force a skill when you want a specific one.

Finish: `/verify-done` before saying done, `/review-checklist` before the PR, `/finish-branch` to land it, `/compact` to hand off.

## 7. Common tasks

| Task | Say or type | What happens |
|---|---|---|
| New feature | *"add dark mode to the settings page"* or `/feature …` | risk intake → lane → plan → build → self-review → commit. A hard gate (auth, payment, migration) asks you to confirm the spec first |
| A ticket by id | `/ticket 412` · `/ticket 412 413 414` | the ticket's intent, spec and plan are written into `docs/tickets/<id>/`, built through `/feature`, one worktree and one PR per ticket; the commit waits for the plan's skills |
| A bug | `/fix-bug uploads over 10 MB crash` | reproduce in a red loop → minimise → hypothesis → fix → regression test. The reproducing test is locked while the fix is written |
| An endpoint, a table, a screen, an API client | `/api-endpoint` · `/db-change` · `/ui-feature` · `/api-client` | built the way the repo already does it, with the layer's test matrix |
| Match a Figma design | `/design-ui <link>` · `/agent-design-ui <link>` for a chat | frames exported, tokens mapped, primitives built once, screenshot diff at the frame size and narrow widths |
| Design first | `/brainstorming <idea>` → `/grill` → `/writing-plans` | `specs/<slug>/design.md`, hardened, then `PLAN.md` with a verify command per task |
| Review | `/review-checklist` · `/blast-radius` · the built-in `/code-review` | numbered findings with the failing case, the fix and the cost of skipping it |
| Answer the review | `/resolve-pr-feedback` | every open thread: fix, answer or decline with a reason, one push, a reply on each |
| PR text only | `/create-pr` | title, summary (why), tasks, file table; nothing is pushed |
| Red build | `/ci-triage` | regression, flaky or environment, with a one-sentence root cause |
| Release | `/release-checklist <version>` | stops on the first unmet item; a mobile production release also needs the approved `release/<version>` commit |
| Schema change | `/write-migration` | expand/contract, backfill separated, down path tested; always high-risk |
| Production incident | `/incident` | timeline, severity, mitigate first, then root cause, regression test and postmortem |
| AI assistant | describe it → `/agent-feature <capability>` → `/agent-verify-turn` → `/agent-evals` → `/agent-security` | see [`plugins/agent/README.md`](../plugins/agent/README.md) |
| Quick question | `/btw <question>` | answered without touching the task |

## 8. Team workflow

- `/sync-memory` at the start of a session: fetches and pulls, scans your commits since the last sync into `.claude/memory/commits/`, lists teammates' commits and flags files you both touched.
- Everyone installs from the same marketplace, so a skill or hook change reaches the team on `/plugin marketplace update harness` (GitLab after `/sync-remote` has mirrored it).
- Project rules and docs travel in the repo (`.claude/docs/`, `.claude/rules/`, `CLAUDE.md`), kept current by `/docs-sync` at the end of each feature.
- `/retro` (lead) at the end of a week reads commits, PRs, reverts and CI failures and proposes what to standardise next.

## 9. Ending a session

- `/compact` when the conversation is long or you are leaving: summarises the work, writes `specs/HANDOFF.md` for the next session, merges learnings into memory. The `compact-advisor` hook suggests it past 200k tokens of context.
- `/compound` after a session with a hard bug or a decision worth keeping: writes a lesson to `docs/solutions/`. Lessons are also captured on their own: `learn-capture` proposes them every 50 tool calls from a scrubbed digest, and `learn-promote` lands the valid ones at the next session start.

## 10. Updating

```text
/plugin marketplace update harness      # plugins, from the source you added
```

```bash
git -C <kit-dir> pull && bash <kit-dir>/scripts/install.sh    # only when global/CLAUDE.md, rules/ or the plugin list changed
bash <kit-dir>/plugins/core/scripts/init.sh /path/to/project   # refresh a project's .claude/; warns before overwriting settings.json
```

Hook and CI changes take effect in a new session, not the current one. Plugin versions stay at `1.0.0` until the kit is published, so after a merge the update step above is what brings the new copy.

## 11. Troubleshooting

**Push or commit blocked.** The hook prints the reason. `branch-guard`: you are on `main` or an environment branch; branch first (`git switch -c feat/<slug>`). `ticket-gate`: a skill the ticket's `plan.md` names has not run; run it, or waive it in `plan.md` with `skip /<skill>: <reason>`. `weakened-check`: the commit deletes a test or loosens a check; confirm or restore it. `commit-quality-gate` (guards): a secret or debug artifact is staged; move the value to `.env` and read it from the environment.

**Claude refuses to read `.env`.** That is `secret-guard`. Give it the value in chat, or run the copy yourself (`cp .env.example .env`). The repo's `.claude/secret-paths.txt` adds patterns to guard; `CLAUDE_SECRET_GUARD=0` turns the guard off for one session.

**An edit through the shell was blocked.** `edit-guard`: change repo files with Edit/Write so the lint and format hooks run; scratch output goes outside the repo or to a gitignored path.

**A skill did not fire, or the wrong one did.** Name it: `/fix-bug …`, or `/<plugin>:<skill>` when two plugins define the same name. From a clone, `bash scripts/check.sh` runs the routing eval; `/diagnose-session` (lead) reads the transcript and says why.

**`HANDOFF.md` not loading.** The project `CLAUDE.md` must contain the Session Resume line `cat specs/HANDOFF.md 2>/dev/null && rm -f specs/HANDOFF.md`, or `guards` must be installed (its `session-resume` hook injects it).

**Claude forgot last session.** `/compact` was not run, or `MEMORY.md` is empty. Claude Code truncates `MEMORY.md` after 200 lines: delete stale entries and their files.

**GitLab asks for a password or times out.** Check the VPN and your SSH key, or add the GitHub mirror instead.

**A plugin is installed but its skills are missing.** Run `/reload-plugins` or open a new session; check `claude plugin list` for a dependency that is disabled and pin it as in section 2.

## 12. Cheat sheet

| Command | When |
|---|---|
| `/project-init` | once per repo, and after a big architecture change |
| `/sync-memory` | start of a session on a team project |
| `/feature <desc>` · `/ticket <id>` | a new capability · a tracker ticket |
| `/fix-bug <symptom>` | something broken, failing or slow |
| `/tdd` | build test-first from a plan task |
| `/brainstorming` → `/grill` → `/writing-plans` | design before a complex feature |
| `/verify-done` · `/checkpoint` | before saying done · progress plus gates |
| `/review-checklist` · `/blast-radius` | before the PR |
| `/finish-branch` | land or park the branch |
| `/ci-triage` · `/release-checklist` · `/incident` | red build · release · outage |
| `/agent-architect` · `/agent-feature` · `/agent-verify-turn` | start · grow · prove an AI assistant |
| `/compact` · `/compound` | end of session · a lesson worth keeping |
| `/btw <question>` | a quick question without breaking the flow |
