# Claude Harness

**Claude Code that follows your team's process, not just your prompt.**

Claude Code writes code fast. Left alone it also skips the plan, commits to `main`, says "tests pass" without running them, and forgets everything when the session ends. Claude Harness is a set of Claude Code plugins that fixes that. It gives Claude the workflows a senior engineer follows (design before code, test-first, review before the PR, evidence before "done"), enforces the non-negotiable ones with hooks that block the commit, and routes expensive decisions to the strong model while cheaper models do the typing. A team that adopts it gets the same process on every machine from one install command, and a reviewer who sees what actually ran instead of what Claude claimed.

- **If you manage the team:** AI-written code becomes safer to accept. Every shortcut shows up as a blocked step with a reason, not as a surprise in production.
- **If you are a senior engineer:** it is a marketplace of role plugins (skills, hooks, rules) with declared dependencies, routing tests that run free on every change, and the design decisions written down. [`DESIGN.md`](DESIGN.md) has the why.
- **If you build AI assistants:** the `ai` role pack takes a chatbot from one plain-language sentence to a scaffolded, traced and evaluated CopilotKit + LangGraph / Mastra app, asking the product questions before any technology.

Live docs: **https://thgwan-claude-harness.vercel.app**. Interactive map of every plugin, skill and hook: [`docs/skill-map.html`](docs/skill-map.html).

## Quickstart

Inside Claude Code, add the marketplace from **one** of the two sources. Both hold the same commit, kept in step with `/sync-remote`:

| Source | Use it when | Command |
|---|---|---|
| **GitLab** (team) | On the company network or VPN, with Reporter access and an SSH key on GitLab | `/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git` |
| **GitHub** (public mirror) | Outside the VPN, or without GitLab access | `/plugin marketplace add thanghokdps/claude-root` |

Install the role you are, then reload. A role brings its dependencies with it:

```text
/plugin install dev@harness        # every developer: plan, build, fix, review (brings core, plan, review, progress)
/plugin install harness@harness    # the whole process kit: all eight general plugins
# role packs (frontend, backend, mobile, ai) and the workplace domain pack are turned on per repo by core's repo-profile hook;
# to force one: /plugin install frontend@harness
/reload-plugins
```

Open Claude Code in your project and say what you want in your own words. Skills fire from the sentence; the slash command is optional:

```text
/project-init                                   # once per existing repo: writes .claude/ docs, rules, memory
add CSV export to the reports page              # a feature: lane chosen, plan, build, review
the upload crashes on files over 10 MB          # a bug: /fix-bug builds a red loop before touching code
Tôi muốn làm một chatbot tra cứu đơn hàng       # an assistant: /agent-architect interviews, then scaffolds
```

Update later with `/plugin marketplace update harness`. The always-loaded global rules (`~/.claude/CLAUDE.md`, `~/.claude/rules/`) come only from a clone plus `bash scripts/install.sh`; the plugins work without them. Install detail, project bootstrap and troubleshooting: [`docs/USAGE.md`](docs/USAGE.md).

## What changes for a team

| Before | With the harness | Enforced by |
|---|---|---|
| "Done" means Claude said so | `/verify-done` re-runs the checks in the session and reports their output; a PR's Witness line is filled from the command log, never typed | `core`, `guards` |
| Code lands on `main` or `staging` straight from a session | Pushes to `main` and environment branches are blocked; work goes through a branch and a PR | `branch-guard` hook, always on |
| A fix "passes" by editing the test | The test that reproduces a bug is locked while the fix is written | `test-lock` hook |
| A secret file is read into the context | `.env*`, keys and service-account files are never read, printed or edited; Claude asks you for the value | `secret-guard` hook |
| A ticket skips review under time pressure | A ticket's commit waits for the skills its plan names; its PR waits for `/verify-done` and `/review-checklist` | `ticket-gate` hook |
| Every step runs on the most expensive model | Opus plans, decides and reviews; Sonnet writes code from an approved plan; Haiku does mechanical work | `model-cost` rule, each skill's `model:` |
| Each session starts from zero | `/compact` writes a handoff the next session reads; `/compound` keeps the lessons in `docs/solutions/` | `core` |

Every gate has a written waiver, so a skipped step is a recorded decision rather than a silent omission. Hooks exit 0 or 2 and never crash the session. Anything beyond the core gates is opt-in (`guards`).

## How it works

Four layers, each loaded at a different time, so the always-on context stays small:

| Layer | Loaded | What it holds | Example |
|---|---|---|---|
| **Rules** | every session, or only for matching file paths | the non-negotiables: git, security, code quality, model cost, testing | never commit to `main`; parameterised queries only |
| **Skills** | on demand, routed from your sentence by each skill's description | a step-by-step workflow with a "Done when" check | `/fix-bug`, `/review-checklist`, `/agent-feature` |
| **Hooks** | on events: session start, before a tool runs, on stop | the checks that must happen, not just be remembered | block a commit, lock a test, show a skill's checklist |
| **Memory** | per project, written by the skills | project docs, handoffs, solutions, team sync | `.claude/docs/`, `specs/HANDOFF.md` |

A request moves through them like this:

```text
your sentence
  → routing    the skill whose description matches fires (tested on every kit change, no model call)
  → lane       tiny: just do it · normal: plan mode → build → verify · high-risk: spec → confirm → build → review
  → build      Opus plans, a cheaper subagent writes, hooks watch every tool call
  → evidence   /verify-done, /review-checklist, then /finish-branch opens the PR
  → memory     /compact (handoff) · /compound (lessons) · /docs-sync (project docs)
```

The lane comes from risk; a human is asked only to resolve ambiguity, never to classify risk. Auth, data migration, security, external providers, public contracts and weakened validation are always high-risk. The control model in full: [`HARNESS.md`](HARNESS.md).

## The plugins

One marketplace, `harness`, one plugin per role. Installing a role pulls in what it depends on. Nothing blocks a commit beyond the core gates unless you install `guards`.

| Plugin | Who installs it | Brings | Depends on |
|---|---|---|---|
| [`core`](plugins/core/README.md) | everyone, through any role | `/verify-done`, `/project-init`, `/docs-sync`, `/compact`, `/compound`, `/sync-memory`, `/btw`; the always-on safety hooks | progress |
| [`plan`](plugins/plan/README.md) | architects, tech leads | `/kickoff`, `/brainstorming`, `/grill`, `/domain-model`, `/codebase-design`, `/writing-plans` | progress |
| [`review`](plugins/review/README.md) | reviewers | `/review-checklist`, `/review-diff`, `/blast-radius`, `/create-pr`, `/resolve-pr-feedback`, `/debt-ledger`, `/repo-audit` | progress |
| [`dev`](plugins/dev/README.md) | every developer | `/feature` (dispatches slices to the role packs' engineers), `/ticket`, `/fix-bug`, `/tdd`, `/resolve-question`, `/checkpoint`, `/coordinator`; the ticket and test-lock hooks | core, plan, review |
| [`frontend`](plugins/frontend/README.md) | web UI repos, turned on per repo | the `frontend-engineer` agent, `/ui-feature`, `/design-ui`; React and Next.js rules | progress, dev |
| [`backend`](plugins/backend/README.md) | server repos, turned on per repo | the `backend-engineer` agent, `/api-endpoint`, `/db-change`, `/api-client`; Python, FastAPI and Prisma rules | progress, dev |
| [`ship`](plugins/ship/README.md) | release and CI owners | `/finish-branch`, `/ci-triage`, `/release-checklist`, `/write-migration`, `/incident`, `/sync-remote`; the mobile release gate | core |
| [`mobile`](plugins/mobile/README.md) | React Native / Expo repos, turned on per repo | the `mobile-engineer` agent, `/mobile-feature`; React Native rules | progress, dev |
| [`ai`](plugins/ai/README.md) | AI-assistant repos, turned on per repo | the `ai-engineer` agent, `/agent-architect`, `/agent-feature`, `/agent-tool`, `/agent-hitl`, `/agent-graph`, `/agent-frontend`, `/agent-design-ui`, `/agent-rag`, `/agent-evals`, `/agent-verify-turn`, `/agent-security`, `/agent-prompt-review`; the framework rules | progress, dev |
| [`workplace`](plugins/workplace/README.md) | teams building HR / workplace apps | `/workplace-review` and the domain invariants; turned on per repo | progress |
| [`lead`](plugins/lead/README.md) | process owners | `/retro`, `/diagnose-session`, `/writing-skills` | core |
| [`guards`](plugins/guards/README.md) | anyone who wants stricter rails | opt-in hooks: commit quality gate, scope gate, blast radius, run log, push evidence, session handoff | dev |
| [`progress`](plugins/progress/README.md) | comes with every role | a skill's checklist and live ✅ progress; never blocks | — |
| [`harness`](plugins/harness/README.md) | "give me everything" | the eight general plugins above; the role packs `frontend`, `backend`, `mobile`, `ai` and the domain pack `workplace` stay separate so they can turn on per repo | all eight |

Today: 11 plugins, 54 skills, 9 always-on rules, 8 recorded design decisions. The index with every skill: [`plugins/README.md`](plugins/README.md).

## Read next

| You want to… | Read |
|---|---|
| Install step by step, bootstrap a project, fix a blocked commit | [`docs/USAGE.md`](docs/USAGE.md) |
| Understand the control model: lanes, hard gates, what hooks enforce | [`HARNESS.md`](HARNESS.md) |
| See why it is built this way: packaging, layers, where each AI-assistant concern lives | [`DESIGN.md`](DESIGN.md) |
| Read one decision and its trade-off | [`docs/ddr/`](docs/ddr/README.md) |
| Build an AI assistant | [`plugins/ai/README.md`](plugins/ai/README.md) |
| Browse every skill and hook visually | [`docs/skill-map.html`](docs/skill-map.html) |

## For kit contributors

`bash scripts/check.sh` runs every free check: skill lint with the dependency check, the routing eval (three prompts per skill must rank it in the top 3, no model call), the hook tests and `claude plugin validate` per plugin. CI runs the same script. Behaviour evals with a real model are paid and run before a release: `bash scripts/eval-plugin.sh <plugin>`. How to add a skill, rule or hook: [`CLAUDE.md`](CLAUDE.md).
