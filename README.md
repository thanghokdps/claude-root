# Claude Harness — build AI assistants with Claude Code

A Claude Code kit centred on **building one AI assistant end to end** on CopilotKit v2 · AG-UI with Mastra, LangChainJS or LangGraph: architecture interview → scaffold → features and tools → chat UI → evals and tracing → security. That is the `agent` plugin. The other plugins are supporting tooling for the everyday dev loop (plan, build, review, ship) and are optional.

**Design:** [`DESIGN.md`](DESIGN.md) — why role plugins, the layers, and where each AI-assistant concern lives (CopilotKit, tools, memory, evals, observability). **Map:** [`docs/skill-map.html`](docs/skill-map.html) — every plugin, skill and hook, interactive.

## Quickstart — AI assistant

Inside Claude Code, add the kit from **one** of two sources. Both hold the same commit, kept in step with `/sync-remote`:

| Source | Use it when | Add the marketplace |
|---|---|---|
| **GitLab** (team) | You are on the company network or VPN, with Reporter access to `thang.hoquang/claude-kit` and an SSH key on GitLab | `/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git` |
| **GitHub** (public mirror) | Outside the VPN, or without GitLab access | `/plugin marketplace add thanghokdps/claude-root` |

Then, whichever source you added:

```bash
/plugin install agent@harness          # pulls in its own dependencies automatically
/reload-plugins
```

`agent` only works with its dependency chain enabled: `agent` → `progress`, `dev`, `ship`; `dev` → `core`, `plan`, `review`. Check with `claude plugin list` that these **seven** are `✔ enabled` in the project: `progress core plan review ship dev agent` (all `@harness`). `lead`, `guards` and the `harness` bundle are not needed. If one is missing or disabled (an older install, or a plugin turned off at another scope), pin the set in the project's `.claude/settings.json`:

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

MCP servers the skills use when present (`claude mcp list`): **Playwright** (`claude mcp add playwright -- npx -y @playwright/mcp@latest`) so the skeleton check and `/agent-frontend` render the chat in a real browser at desktop and 375 px; **Figma** only for `/agent-design-ui` from a Figma link.

Update later with `/plugin marketplace update harness`. It pulls from the source you added. If git asks for a password or times out on GitLab, check the VPN and your SSH key, or use GitHub.

Then open Claude Code in an empty folder and **say what you want to build, in your own words**. No command to remember:

```text
Tôi muốn làm một chatbot giúp khách tra cứu và đổi địa chỉ đơn hàng
```

Claude picks the right skill from that sentence (here `agent-architect`) and **asks before it builds**, one question per turn, each with a recommendation:

1. **The problem:** who uses it and why, the 3–5 things users will ask (with one real example message each), the systems it reads or writes, and what it must refuse.
2. **The choices that are costly to change:** host, clients, single app or monorepo. Everything else is defaulted and shown on one card for you to confirm. Design is never asked: give a Figma link or mockup in your request if you have one; without one the chat is CopilotKit's stock `CopilotChat` with theme tokens.
3. **Then it builds:** checks Node, the package manager, the model key and git; writes the architecture record (`docs/adr/`); scaffolds the smallest slice; and proves it with one real streamed turn.

**Just the frame, no features yet?** One sentence in an empty folder is enough: say *init* or *dựng*, name whatever parts of the stack you care about, and do not say what the chatbot does.

```text
init chatbot <empty | no features> [with <framework>] [+ <frontend>] [+ <database>] [+ <auth>] [, tracing with <provider>]
```

For example:

- *"init chatbot empty features, dùng Mastra, tracing bằng Langfuse"*
- *"Dựng skeleton chatbot rỗng bằng Next.js + CopilotKit + LangGraph + Postgres, chưa cần feature gì"*
- *"init codebase chatbot assistant empty feature, langchain framework, tracing with langsmith"*

Each named piece is taken as given; anything you leave out is defaulted, never asked:

| You say | It builds | Default when not said |
|---------|-----------|-----------------------|
| Framework: *LangChain* / *LangGraph* | shape A, `createAgent` on the LangGraph runtime | asked once: the only question (with the frontend and database) |
| Framework: *Mastra* | shape M, one `new Mastra({ agents, … })` | |
| Framework: *custom LangGraph graph* / *StateGraph* | shape B, your own graph + AG-UI emitter | |
| Frontend: *Next.js*, *Vite*, *React Router* | that app with the CopilotKit runtime | Next.js App Router |
| Database: *Postgres + Drizzle*, *Prisma*, *SQLite* … | connection + migrations only | none (in-memory threads, dev only) |
| Auth: *Better Auth*, *Clerk*, *NextAuth*, SSO | that login feeding the agent's trusted context | a dev user, refused in production |
| Tracing: *Langfuse*, *LangSmith* … | that provider behind one switch, content masked | the switch with `none` |
| Model provider | the provider whose key you have | the one preflight finds |

Only when you describe what the assistant helps with does Claude run the full interview and plan above.

`agent-architect` switches to **skeleton** mode, shows those defaults in one table you can change later, and in the same turn:

1. **Preflight:** git, Node, the package manager, a model key (name only) and a git repo; it runs `git init` itself.
2. **Scaffold** from the vendor's reference repo at a resolved SHA, with exact pins: the env schema that fails at boot, the caller's identity, one agent with no tools, the model factory (primary, fallback, cheap), the tracing switch with masking on, and the stock chat UI with your theme tokens. No tools, no confirm cards and no domain tables (a database you named gets its connection and migrations only).
3. **Your one step:** the secret guard never lets Claude create or read `.env`, so it asks you to run `! cp .env.example .env` and fill the model key. Every value that is not a secret is already filled in `.env.example`.
4. **Proof:** `pnpm dev`, then one real streamed "hello" turn through the web route (`RUN_STARTED → TEXT_MESSAGE_* → RUN_FINISHED`).
5. **Docs:** `/project-init` writes `CLAUDE.md`, `AGENTS.md` (when another coding agent is used) and `.claude/docs/`, and the ADR records the stack, the defaults card and what was deferred.

The repo it leaves (single-app layout; a monorepo you name moves the same parts under `apps/` and `packages/`). Only the agent folder changes with the framework, following that vendor's reference repo:

```
.env.example                 # every name; non-secrets filled
src/app/page.tsx             # stock CopilotChat bound to the agent id
src/app/api/copilotkit/…     # CopilotRuntime route: 401 guard, verified caller → agent
src/server/                  # env schema, identity (your auth, or the dev user)
src/styles/tokens.css        # design tokens + CopilotKit theme
<agent folder>               # one agent "assistant", no tools, + ids · env · identity · models · tracing
docs/adr/0001-agent-architecture.md
AGENTS.md · CLAUDE.md · .claude/docs/
```

| Framework | `<agent folder>` |
|-----------|------------------|
| LangChain / LangGraph (A) | `agent/` package: `langgraph.json`, `src/<agent>/` (`createAgent`, prompt, per-turn factory), served by `langgraphjs dev` |
| Custom LangGraph graph (B) | `agent/` package: `src/<graph>/{graph,state,prompts}.ts` + the AG-UI emitter |
| Mastra (M) | `src/mastra/`: `index.ts` (`new Mastra`), `agents/assistant.ts`, `observability` for tracing |

It ends by listing the features still to build, each as the sentence to give `agent-feature`. Tests and evals are part of the skeleton; say *"chưa cần test"* and they are skipped and recorded as deferred on the ADR. Changing the framework while the skeleton has no features rebuilds the skeleton; once features exist, it is a planned migration. Full rules: [`skeleton.md`](plugins/agent/skills/agent-architect/references/skeleton.md).

After that, ask for each feature the same way, e.g. *"Thêm tính năng cho khách đổi địa chỉ giao hàng"*. `agent-feature` checks it against the architecture record, asks what is unclear, reuses what exists, and builds it layer by layer.

Say it in plain words, as above. The command column is what fires, and what to type only when you want to force it:

| I want to… | Fires |
|---|---|
| Start an assistant, an empty skeleton on my stack, or audit one | `/agent-architect` (`greenfield` · `skeleton` · `audit`) |
| Add a feature | `/agent-feature` (it calls the layer skills below in order) |
| Add a backend tool · a frontend tool | `/agent-tool` · `/agent-frontend` (`useFrontendTool`) |
| Confirm before a write | `/agent-hitl` |
| Fix routing, add an agent, rewrite a prompt | `/agent-graph` |
| Wire CopilotKit, suggestions, shared context | `/agent-frontend` |
| Turn a Figma design into the chat UI | `/agent-design-ui <figma>` |
| Turn a Figma design into any other page | `/design-ui <figma>` |
| Backend endpoint · DB change · React screen · call an API | `/api-endpoint` · `/db-change` · `/ui-feature` · `/api-client` (dev) |
| Prove a change works | `/agent-verify-turn local` |
| Eval dataset, prompt evals, tracing | `/agent-evals dataset` · `suite` · `observability` |
| Security review | `/agent-security` |

Skills fire on their own from what you type; the slash command is optional. A vague request gets questions first, never a guessed build. Details and the rules each skill follows: [`plugins/agent/README.md`](plugins/agent/README.md).

## Quickstart — the whole kit (optional)

Install everything (`agent` plus the dev-loop plugins and global rules) when you also want the general workflow:

```bash
# Inside Claude Code
/plugin install harness@harness

# Or from a clone, which also installs global/CLAUDE.md and the global rules.
# Clone anywhere — install.sh resolves its own location. From GitLab (VPN + SSH key)…
git clone git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git <any-dir>/harness
# …or from the GitHub mirror (same commit):
# git clone git@github.com:thanghokdps/claude-root.git <any-dir>/harness
bash <any-dir>/harness/scripts/install.sh        # no env vars needed; see .env.sample for optional ones
```

Bootstrap a project:

```bash
# Existing repo
cd my-project && claude
/project-init                                       # scans the repo, writes .claude/ docs, rules, memory

# Empty folder (not an AI assistant — for one, describe it in plain words as above)
mkdir my-app && cd my-app && git init && claude
/kickoff <your PRD, ERD, ADR, stack docs>           # reads what you have, grills only the gaps → docs/kickoff.md
/brainstorming <idea>                               # only if an approach is still open → specs/<slug>/design.md
/writing-plans                                      # → PLAN.md; wave 1 = scaffold (manifest, tests, lint)
# build wave 1 (just ask, or /tdd), commit, then:
/project-init                                       # now there is a stack and code to scan
```

| I want to… | Run |
|---|---|
| Build a feature / fix a bug | just describe it (auto-coordinator) · `/fix-bug <symptom>` |
| Start a project from our docs | `/kickoff` → `/writing-plans` (or `/agent-architect` for an assistant) |
| Design before coding | `/brainstorming` → `/writing-plans` |
| Review before a PR | `/review-checklist` → `/code-review` |
| Finish the branch | `/verify-done` → `/finish-branch` |
| End the session | `/compact` (handoff) · `/compound` (learnings) |

Full skill list: [`plugins/README.md`](plugins/README.md). Step-by-step guide: [`docs/USAGE.md`](docs/USAGE.md). Everything below this point is reference for the whole kit.

---

## Table of Contents

1. [How it works](#how-it-works)
2. [Repository structure](#repository-structure)
3. [Installation](#installation)
4. [Bootstrapping a project](#bootstrapping-a-project)
5. [Skills reference](#skills-reference)
6. [Hooks reference](#hooks-reference)
7. [Rules reference](#rules-reference)
8. [Agents reference](#agents-reference)
9. [Commands reference](#commands-reference)
10. [Stack bundles reference](#stack-bundles-reference)
11. [Scripts reference](#scripts-reference)
12. [Templates reference](#templates-reference)
13. [Memory system](#memory-system)
14. [The coordinator flow](#the-coordinator-flow)
15. [Risk lanes & hard gates](#risk-lanes--hard-gates)
16. [Extending the harness](#extending-the-harness)

---

## How it works

Two layers:

| Layer | What it is | Lives in |
|-------|-----------|---------|
| **Skills** (engine) | Invocable `/skills` that do the work — feature, fix-bug, review, verify | `skills/`, `agents/` |
| **Harness** (control) | Thin governance layer that determines risk, routes work, enforces gates | `plugins/guards/hooks/`, `rules/`, memory system |

The engine answers *"how do I build this?"* The harness answers *"how careful should I be, and who needs to approve?"*

**Core principle:** Ceremony scales with risk. Human interruption scales with ambiguity.

- **Risk** → how much proof and process (lanes: tiny / normal / high-risk)
- **Ambiguity** → whether a human is asked (only to confirm intent, not classify risk)

### Request lifecycle

```
prompt
  → scope-gate.sh          (classify risk, warn on stale memory)
  → /coordinator            (route to the right agent sequence)
  → Explorer / Planner      (understand + plan)
  → Implementer / Debugger  (build)
  → Verifier / Reviewer     (prove)
  → commit-quality-gate.sh  (block bad commits)
  → save-commit-memory.sh   (persist to memory)
  → session-handoff.sh      (write HANDOFF.md on session end)
```

---

## Repository structure

```
<kit-dir>/                           ← this repo (the source library)
├── CLAUDE.md                        ← project instructions for Claude Code
├── DESIGN.md                        ← packaging, layers, AI-assistant design
├── HARNESS.md                       ← philosophy / architecture reference
├── PLAYBOOK.md                      ← playbook reference
├── README.md                        ← this file
│
├── .claude-plugin/
│   └── marketplace.json             ← lists the 10 plugins below
│
├── plugins/                         ← role plugins (self-contained, each with plugin.json)
│   ├── README.md                    ← plugin index, skill table, handoff map
│   │
│   ├── progress/              ← skill checklist + live ✅ progress (hooks only, never blocks)
│   │   └── hooks/
│   │       └── skill-progress.sh
│   │
│   ├── core/                  ← session + project basics every role uses
│   │   ├── hooks/stacks/            ← stack-specific hooks (eslint, ruff)
│   │   ├── memory/                  ← memory templates (MEMORY.md.template, user.md, project.md)
│   │   ├── rules/                   ← universal rules (behavior, git, security, testing, etc.)
│   │   │   └── stacks/             ← stack-specific rules (fastapi, nextjs, python, etc.)
│   │   ├── scripts/init.sh          ← bootstrap .claude/ for a project (stack-aware)
│   │   ├── skills/                  ← btw, compact, compound, docs-sync, project-init,
│   │   │                               sync-memory, verify-done
│   │   ├── stacks/                  ← full stack bundles (nextjs, python, react-native)
│   │   └── templates/               ← CLAUDE.md.template, settings.json.template, etc.
│   │
│   ├── plan/                  ← design before code
│   │   └── skills/                  ← kickoff, brainstorming, codebase-design, domain-model,
│   │                                   grill, writing-plans
│   │
│   ├── review/                ← review diffs, PRs, impact
│   │   └── skills/                  ← blast-radius, create-pr, debt-ledger, repo-audit, review-checklist, review-diff
│   │
│   ├── dev/                   ← build, fix, test-first
│   │   └── skills/                  ← checkpoint, coordinator, feature, fix-bug, tdd
│   │
│   ├── ship/                  ← release / CI owner
│   │   └── skills/                  ← ci-triage, finish-branch, release-checklist, write-migration
│   │
│   ├── agent/                 ← AI-agent engineer (CopilotKit, LangGraph)
│   │   ├── evals/                   ← routing + behaviour eval cases
│   │   ├── rules/                   ← agent-specific invariants (read on demand)
│   │   └── skills/                  ← agent-architect, agent-design-ui, agent-evals,
│   │                                   agent-feature, agent-frontend, agent-graph,
│   │                                   agent-hitl, agent-security, agent-tool, agent-verify-turn
│   │
│   ├── lead/                  ← process owner: retro, diagnosis, skill authoring
│   │   └── skills/                  ← diagnose-session, retro, writing-skills
│   │
│   ├── guards/                ← personal guard-rail hooks (opt-in)
│   │   └── hooks/                   ← hooks.json + 14 bash scripts
│   │       ├── hooks.json           ← hook registration (uses ${CLAUDE_PLUGIN_ROOT})
│   │       ├── scope-gate.sh        ← inject coordinator context on every prompt
│   │       ├── commit-quality-gate.sh ← block secrets / debug artifacts
│   │       ├── risk-corroboration.sh ← block commits when diff risk > declared lane
│   │       ├── blast-radius-check.sh ← warn on edits outside plan scope
│   │       ├── format-on-edit.sh    ← run formatter after editing files
│   │       ├── headroom-compress.sh ← auto context compression on large outputs
│   │       ├── save-commit-memory.sh ← persist commit info to memory
│   │       ├── session-handoff.sh   ← write HANDOFF.md on session end
│   │       ├── session-resume.sh    ← load HANDOFF.md on session start
│   │       ├── state-breadcrumb.sh  ← append session breadcrumb to memory
│   │       ├── notify-on-finish.sh  ← notification on session end
│   │       └── agent-progress.sh    ← colorized live agent/wave progress
│   │
│   └── harness/                   ← bundle (depends on all nine above)
│
├── global/
│   └── CLAUDE.md                    ← installed to ~/.claude/CLAUDE.md
│
├── docs/
│   └── USAGE.md                     ← usage documentation
│
├── eval/                            ← evalkit — code quality evaluation harness
│   ├── evalkit/                     ← runner, sandbox, judges, graders
│   └── tasks/                       ← golden tasks for benchmarking
│
├── scripts/                         ← kit tooling (not shipped to projects)
│   ├── install.sh                   ← one-command harness install + ~/.claude/ sync
│   ├── check.sh                     ← lint + trigger eval + validate
│   ├── eval-plugin.sh               ← run plugin evals
│   ├── eval-triggers.py             ← trigger evaluation
│   ├── lint-kit.py                  ← kit linter
│   ├── setup-headroom.sh            ← install headroom context compression
│   └── setup-mcp.sh                 ← MCP server setup
│
└── specs/                           ← active spec workspace
```

---

## Installation

### One-time global install

```bash
bash <kit-dir>/scripts/install.sh     # <kit-dir> = wherever you cloned the kit
```

Installs `global/CLAUDE.md` and `plugins/core/rules/` into `~/.claude/`, registers this directory as the local marketplace `harness` (or keeps `harness` from GitLab or GitHub if you already added it there), and installs every role plugin plus the `harness` bundle (from a local folder, kit edits are live in new sessions). It backs up what it replaces and migrates an old copy-based or 2.x single-plugin install.

The kit is split by role — see [`plugins/README.md`](plugins/README.md). Installing a role plugin installs its dependencies: `dev` brings `core`, `plan`, `review`; `agent` brings `dev` and `ship` (and through them `core`, `plan`, `review`), because its skills hand off to `/fix-bug`, `/verify-done`, `/review-checklist`, `/write-migration` and `/finish-branch`; hooks are the opt-in `guards`, except `branch-guard`, which ships in `core` and is always on.

Instead of a local clone, add the marketplace from GitLab (VPN + SSH key) or from GitHub. Run one of these two lines; the source table in the Quickstart says which:

```
/plugin marketplace add git@gitlab.asoft-python.com:thang.hoquang/claude-kit.git
```

```
/plugin marketplace add thanghokdps/claude-root
```

Then:

```
/plugin install agent@harness     # one role (+ its dependencies)
/plugin install harness@harness       # everything
```

**Update:** skills/hooks — nothing to do for a local install (loaded in place); GitLab or GitHub install → `/plugin marketplace update harness` (kit changes reach GitLab through `/sync-remote`). A new plugin, `global/CLAUDE.md` or `rules/` changed → re-run `install.sh` (`plugin update` does not install a dependency a new version adds).

**Check before committing:** `bash scripts/check.sh` (skill lint incl. the plugin dependency check, trigger eval, `claude plugin validate` per plugin).

### Optional: context compression (headroom)

Headroom automatically compresses large tool outputs to reduce token usage.

**Requires:** Python 3.12 (`brew install python@3.12`) and the `claude` CLI.

```bash
bash <kit-dir>/scripts/setup-headroom.sh
```

What it does:
1. Creates a virtualenv at `~/.headroom-env`
2. Installs `headroom-ai[all,mcp]`
3. Registers the headroom MCP server (`headroom_compress`, `headroom_retrieve`, `headroom_stats`)

After setup, the `headroom-compress.sh` hook auto-triggers compression whenever a tool output exceeds ~8 KB.

---

## Bootstrapping a project

Run once per project to generate a tailored `.claude/` workspace.

### Option A — Claude Code (recommended)

```bash
cd my-project
# Open Claude Code, then type:
/project-init
```

The `/project-init` skill scans the codebase, then writes every file in `.claude/` — docs, agents, hooks, rules, skills, templates, and `settings.json` — using real paths and real commands from the project.

### Option B — Shell script

```bash
cd my-project
# Lean bootstrap (shared rules/skills come from installed plugins):
bash <kit-dir>/plugins/core/scripts/init.sh

# Standalone bootstrap (copies rules, skills, commands, agents, hooks into .claude/):
STANDALONE=1 bash <kit-dir>/plugins/core/scripts/init.sh /path/to/my-project
```

### What `init.sh` detects

The script scans manifests and `src/` for signals:

| Signal | Detection trigger |
|--------|------------------|
| `nodejs` | `package.json` exists |
| `typescript` | `tsconfig.json` or `"typescript"` in package.json |
| `nextjs` | `"next"` in package.json |
| `python` | `requirements.txt`, `pyproject.toml`, or `setup.py` |
| `fastapi` | `fastapi` in requirements/pyproject |
| `langgraph` | `langgraph` in requirements or package.json |
| `golang` | `go.mod` |
| `java` | `pom.xml` or `build.gradle` |
| `rust` | `Cargo.toml` |
| `react` | `"react"` in package.json |
| `jest` | `"jest"` in package.json |
| `docker` | `Dockerfile` or `docker-compose.yml` |
| `prisma` | `"prisma"` in package.json or `prisma` in `src/` |
| `postgres` | `postgres` or `pg` in `src/` |
| `redis` | `redis` in `src/` |

### What gets generated

```
your-project/
├── CLAUDE.md                    ← Fill in: run commands, architecture, constraints
└── .claude/
    ├── settings.json            ← Hooks auto-registered, deny-list set
    ├── docs/                    ← Knowledge base (written by /project-init)
    │   ├── index.md
    │   ├── architecture.md
    │   ├── conventions.md
    │   ├── stack.md
    │   ├── entry-points.md
    │   └── test-strategy.md
    ├── rules/
    │   ├── git.md
    │   ├── testing.md
    │   ├── orchestration.md
    │   ├── memory.md
    │   └── <stack>.md           ← Stack-specific rules (typescript, python, etc.)
    ├── skills/
    │   ├── feature/SKILL.md
    │   ├── fix-bug/SKILL.md
    │   ├── review-checklist/SKILL.md
    │   ├── checkpoint/SKILL.md
    │   └── sync-memory/SKILL.md
    ├── hooks/                    ← installed by core (branch-guard) and guards plugins
    │   ├── hooks.json
    │   ├── commit-quality-gate.sh
    │   ├── branch-guard.sh
    │   ├── save-commit-memory.sh
    │   ├── state-breadcrumb.sh
    │   └── scope-gate.sh
    └── memory/
        ├── MEMORY.md            ← Index (loaded every session)
        ├── user.md              ← Fill in: your role, preferences
        ├── project/
        │   └── context.md       ← Fill in: goals, decisions, deadlines
        ├── feedback/            ← Auto-saved from corrections
        ├── commits/             ← Auto-saved after each git commit
        └── sessions/            ← Auto-saved at session end
```

### After bootstrapping — fill in three files

1. **`CLAUDE.md`** — add the actual run commands, architecture summary, and constraints
2. **`.claude/memory/project/context.md`** — add project goals, active decisions, deadlines
3. **`.claude/memory/user.md`** — add your role and working preferences

---

## Skills reference

Skills are slash commands Claude runs as guided workflows. Each lives in `plugins/<plugin>/skills/<name>/SKILL.md`.

### `/coordinator <request>` — Main orchestration hub

**Invoke:** `/coordinator add dark mode to the settings page`

The auto-coordinator is active by default — every prompt is treated as a coordinator request. You do not need to type `/coordinator` explicitly.

**What it does:**

1. **Step 0** — Load `.claude/docs/` and `docs/solutions/INDEX.md` (do not re-scan the codebase if docs exist)
2. **Step 1** — Parse the prompt: extract intent, scope, urgency, and risk signals
3. **Step 2** — Classify into an intent category and assign a lane (tiny / normal / high-risk)
4. **Step 3** — Confidence check (1–5); if ≤ 3 on high-risk, ask before dispatching
5. **Step 4** — Initialize `specs/<slug>/` (SUMMARY.md, TEST_MATRIX.md, ESCALATIONS.md); create TaskCreate entries for every agent step
6. **Step 5** — Wave execution: dispatch all same-wave tasks in a single message with `run_in_background: true`; verify each wave before advancing
7. **Step 6** — Synthesize results; run Verifier; report PASS / FAIL

**Intent categories:**

| Category | Trigger keywords | Default agent sequence |
|---|---|---|
| `new-feature` | add, build, create, implement | Planner → Implementer → Verifier |
| `bug-fix` | fix, broken, crash, not working | Debugger → Implementer → Verifier |
| `refactor` | refactor, clean up, rename, simplify | Refactorer → Verifier |
| `code-review` | review, audit, check | Reviewer |
| `verify` | verify, confirm, does this work | Verifier |
| `explore` | where is, how does, explain, find | Explorer |
| `security` | security, vuln, injection, XSS | Security Reviewer |
| `performance` | slow, optimize, latency, memory leak | Performance Analyst |
| `docs` | document, README, docstring | Doc Writer |
| `question` | conversational, no action implied | Direct answer — no dispatch |

**Output (for normal/high-risk):**
```
Intent:    new-feature · Lane: normal · Confidence: 4/5
Routing:   Planner → Implementer → Verifier
Assumption: none
Specs dir: specs/add-dark-mode/
```

---

### `/feature <description>` — Implement a new feature

**Invoke:** `/feature add CSV export to the reports page`

**Stages:**

| Stage | What happens |
|-------|-------------|
| 0 — Risk intake | Evaluate 10-flag checklist; assign lane (tiny/normal/high-risk) |
| 1 — Research | Does this already exist? Lightest path? Blast radius? (normal+ only) |
| 2 — Plan | Step-by-step plan with exact commands; save to `specs/<slug>/PLAN.md` (high-risk only) |
| 3 — Build | Follow the plan; run quality gates after each chunk |
| 4 — Review | Self-review: security, type errors, debug artifacts; spawn reviewer sub-agent (high-risk) |
| 5 — Commit | `git add <specific files>` + commit; `save-commit-memory.sh` auto-fires |

**Escalation triggers:** confidence drops below medium, hard gate discovered mid-task, scope creep detected, conflicting teammate commit found in memory.

---

### `/fix-bug <symptom>` — Root-cause a bug and apply minimal fix

**Invoke:** `/fix-bug crash when uploading files larger than 10MB`

**Stages:**

| Stage | What happens |
|-------|-------------|
| 1 — Reproduce | Confirm the bug is real; document exact input/output |
| 2 — Root cause | Trace to origin; grep error messages, check git log; max 3 files before asking |
| 3 — Minimal fix | Smallest fix; no refactoring, no renaming, no extra error handling |
| 4 — Verify | Run failing test; re-run scenario; run full test suite; `tsc --noEmit` (TS projects) |
| 5 — Commit | `fix: <what was wrong and what fixed it>` |

**Rule:** Fix ONLY the specific bug. No cleanup, no "while I'm here" changes.

---

### `/review-checklist [PR]` — Review in a fixed order

**Invoke:** `/review-checklist` (current branch) or `/review-checklist 123`

Walks correctness → tests → scale → readability → security → scope, checks the PR description is self-contained, and returns numbered `file:line` findings, each with the concrete case that fails and what happens if it is skipped. Renamed from `code-review` so the built-in `/code-review` and `/code-review ultra` are no longer shadowed — escalate to those for risky branches.

---

### `/kickoff` — Start a project from the documents you have

**Invoke:** `/kickoff docs/PRD.md docs/erd.png <figma link>`

Collects what exists first, in order: requirements → prerequisites → tech stack → ERD → architecture (ADR) → design → external APIs → non-functional → delivery. Reads them into one doc set (`docs/requirements.md`, `docs/stack.md`, `docs/erd.md`, `docs/adr/*` …), shows a coverage matrix in `docs/kickoff.md`, then grills only the missing, partial or conflicting rows, one question at a time. Hands off to `/agent-architect`, `/brainstorming`, `/writing-plans` or `/project-init`, which all read the doc set instead of asking again.

---

### `/brainstorming` — Design-first session before implementation

**Invoke:** `/brainstorming add a notification system`

**Steps:** Explore context → clarify intent (one question at a time) → propose 2–3 approaches with trade-offs → design the chosen approach → review with user → write `specs/<slug>/design.md` → hand off to `/writing-plans`.

**Rule:** Do NOT write any implementation code during brainstorming.

---

### `/writing-plans` — Convert design doc to implementation plan

**Invoke:** `/writing-plans` (run after `/brainstorming`)

**Input:** `specs/<slug>/design.md` (written by `/brainstorming`)

**Output:** `specs/<slug>/PLAN.md` — wave-organized task list with XML tasks, file maps, and verifiable acceptance criteria. Each task has: `wave`, `files`, `action`, `verify` (shell command), `done` (measurable condition).

---

### `/project-init` — Bootstrap `.claude/` workspace for a new project

**Invoke:** `/project-init` (run once per project)

**Steps:**

| Step | Output |
|------|--------|
| 1 — Scan | Detect language, framework, tools, test setup, CI |
| 2 — Write `docs/` | architecture, conventions, stack, entry-points, test-strategy, index |
| 3 — Write `agents/` | implementer, reviewer, verifier (+ project-specific agents) |
| 4 — Write `hooks/` | commit-gate + stack-specific hooks (tsc, ruff, eslint) — via guards plugin |
| 5 — Write `rules/` | project-conventions + stack-specific rules |
| 6 — Write `skills/` | task skill + project-specific skills |
| 7 — Write `templates/` | SUMMARY, TEST_MATRIX, ESCALATIONS adapted to project commands |
| 8 — Write `settings.json` | full permissions + deny list + project hooks |
| 9 — Generate `CLAUDE.md` | project-specific with real paths and commands |
| 10 — Report | Summary of what was generated |

**Rule:** All generated files use real file paths, real commands, and real names from the scan — no boilerplate.

---

### `/compact` — Persist session state before ending

**Invoke:** `/compact` (run when conversation is long or before ending a session)

**What it does:**
1. Run `headroom learn` if installed (mines failures into corrections)
2. Summarize the session (what was done, decisions, discoveries, current state, next steps)
3. Write to `specs/HANDOFF.md` (overwrite — only latest session matters)
4. Merge non-obvious learnings into `docs/solutions/`
5. Update global memory if user-level preferences were learned

**Next session:** Claude reads `specs/HANDOFF.md` automatically via CLAUDE.md, then deletes it.

---

### `/docs-sync` — Keep `.claude/docs/` current after each feature

**Invoke:** `/docs-sync` (runs from `/feature`, `/agent-feature` and `/finish-branch`)

Maps the branch's diff to the docs it makes stale (routes → `entry-points.md`, layers → `architecture.md`, commands and dependencies → `stack.md`, patterns → `conventions.md`), edits only those sections with paths that exist, and commits them with the code. Agents read `.claude/docs/` instead of rescanning, so a stale doc sends them to the wrong place.

---

### `/compound` — Crystallize session learnings into solutions

**Invoke:** `/compound` (run at end of any significant session)

Mines the session for mistakes found, solutions discovered, and patterns identified. Writes them to `docs/solutions/` so future agents don't repeat the same mistakes.

---

### `/sync-memory` — Team sync: pull + rebuild memory

**Invoke:** `/sync-memory` (run at start of each team session)

Delegates to `scripts/sync-team.sh`. What it does:
1. Stash uncommitted changes
2. Find your last known commit (from `memory/commits/last-sync.txt`)
3. `git fetch --all --prune` + `git pull`
4. Collect your commits since last sync → write to `memory/commits/<date>.md`
5. Collect team commits → flag files you both touched
6. Pop stash; update MEMORY.md index

---

### `/debt-ledger [marker]` — List deliberate shortcuts

**Invoke:** `/debt-ledger` (or `/debt-ledger TODO` for another marker)

Greps every `shortcut: <limit>, <when to upgrade>` comment (the convention in `rules/code-quality.md`) into one ledger grouped by file, and tags the ones that name no upgrade trigger `no-trigger`. Read-only.

---

### `/repo-audit [folder]` — Audit a whole codebase

**Invoke:** `/repo-audit` (whole repo) or `/repo-audit packages/api`

Maps the repo first (from `.claude/docs/` when it exists), states the load it assumes, traces the flows where a mistake costs most, then reports at most 20 numbered findings in Must / Should / Nice — bug, risk, scale, missing test, speed, lean — each with the concrete failing case, the fix and what skipping it costs. Ends with a verdict, possible line and dependency cuts, and what it did not check. Read-only; for a diff use `/review-checklist`.

---

### `/review-diff` — Visual diff review with diagrams

**Invoke:** `/review-diff`

Generates a Markdown review of the current git diff including: architecture diagram (Mermaid), component flowchart, and code walkthrough with inline diff blocks.

---

### `/create-pr` — Generate PR description

**Invoke:** `/create-pr`

Fills `PR_TEMPLATE.md` with: title, summary (why not how), tasks completed, file changes table, and notes. Does NOT push or create the PR — outputs the template for review.

---

### `/checkpoint` — Check progress + quality gates

**Invoke:** `/checkpoint`

Reads the active `PLAN.md`, checks each task's status, runs quality gate commands (lint, typecheck, tests), and reports completed vs remaining.

---

### `/btw <question>` — Quick one-off question without interrupting context

**Invoke:** `/btw what does the UserService.findById method return?`

Fast lookup that answers without creating tasks, specs, or side effects. Use mid-task to check something without breaking flow.

---

## Hooks reference

Hooks are bash scripts triggered by Claude Code events. They exit `0` to allow or `2` to block.

### `commit-quality-gate.sh`

**Trigger:** `PreToolUse(Bash)` when command matches `git commit`

**Checks:**

| Check | Pattern | Action |
|-------|---------|--------|
| OpenAI API key | `sk-[a-zA-Z0-9]{20,}` | BLOCK |
| AWS access key | `AKIA[0-9A-Z]{16}` | BLOCK |
| Hardcoded credential | `(password\|secret\|api_key)\s*=\s*"..."` | BLOCK |
| `.env` file staged | `.env`, `.env.local`, `.env.prod*` | BLOCK |
| Python debugger | `breakpoint()` or `pdb.set_trace()` | BLOCK |
| `console.log/debug` | Added lines with `console.log` or `console.debug` | WARN only |
| Large binary file | Staged file > 5 MB | BLOCK (suggest git-lfs) |

Skips test files (`*.test.*`, `*.spec.*`) and docs for credential scanning.

**On block:** exits 2 with `🚫 COMMIT BLOCKED` message listing all reasons.

---

### `branch-guard.sh` (core, always on)

**Trigger:** `PreToolUse(Bash)` when command matches `git push`. Ships in `plugins/core/hooks/`, so every role install has it.

**Checks:**

| Check | Action |
|-------|--------|
| Any direct push to an environment branch: `dev`, `develop`, `stag`, `stage`, `staging`, `prod`, `production` (override with `HARNESS_ENV_BRANCHES="dev qa prod"`; empty turns it off) | BLOCK — merge through a PR |
| Force, delete or mirror push to `main/master` or an environment branch | BLOCK |
| A push whose repository or target it cannot resolve (`cd -`, `~`, a variable, `--git-dir`, a non-repo path), a mirror remote, or a wildcard `remote.*.push` that includes an environment branch | BLOCK (fails closed) |
| A push in a command with `GIT_DIR` / `GIT_WORK_TREE` / `GIT_CONFIG*`, `export`, a `cd` inside `( )`, `{ }` or a loop, `-c remote.*.push` in any letter case, or `--config-env` (quoted text ignored) | BLOCK (fails closed) |
| Commit on `main`, `master` or an environment branch (except the first commit of an empty repo) | BLOCK — create a branch first |
| Direct push to `main` or `master` | WARN |
| Uncommitted local changes, on a push | WARN (changes will not be pushed) |

---

### `edit-guard.sh` (core, always on)

**Trigger:** `PreToolUse(Bash)`, inside a git worktree.

Repo files change through Edit/Write, so the per-edit lint and format hooks see every change.

| Check | Action |
|-------|--------|
| `sed -i`, `perl -i` on a repo file | BLOCK |
| `>`, `>>`, `tee` or a heredoc writing a tracked (not gitignored) repo path | BLOCK |
| An inline `python`/`node`/`ruby` script (heredoc, `-c`, `-e`) that writes a repo file | BLOCK |
| Targets outside the repo, gitignored paths, `.git/`, `/dev/*`; a script kept in a file | allowed |

---

### `ticket-ledger.sh` + `ticket-gate.sh` (dev, always on)

**Trigger:** the ledger on `PostToolUse(Skill|Agent|Task)` and `UserPromptExpansion`; the gate on `PreToolUse(Bash)` for `git commit` / `gh pr create` and on `mcp__github__create_pull_request`.

Applies on a branch `<type>/<id>-<slug>` with `docs/tickets/<id>/plan.md`. The ledger (in `.git/`, never committed) records the skills and subagents that ran on the branch.

| Check | Action |
|-------|--------|
| `plan.md` has no `Risk:` or `Skills:` line | BLOCK commit with code, and PR |
| A skill on the `Skills:` line, or `/agent-verify-turn` when an `/agent-*` skill is listed, never ran | BLOCK commit with code, and PR |
| No subagent ran with `model: sonnet` or `haiku` | BLOCK commit with code, and PR |
| `/verify-done` or `/review-checklist` never ran; on `Risk: high`, `/security-review` or `/code-review` never ran | BLOCK PR |
| `skip /<skill>: <reason>` or `skip subagents: <reason>` in `plan.md` | waives that check, with the reason on record |

---

### `sensitive-path.sh` (core, always on)

**Trigger:** `PreToolUse(Edit|Write|MultiEdit|NotebookEdit|Bash)`.

| Check | Action |
|-------|--------|
| Edit or shell write (`>`, `tee`, `sed -i`, `cp`/`mv` onto it) of a path in `sensitive-paths.txt` or the repo's `.claude/sensitive-paths.txt`: secrets, CI/deploy, Claude settings | ASK the user |
| The path is named in the ticket's `plan.md` or a `specs/*/PLAN.md` | allowed |

### `repo-profile.sh` (core, always on)

**Trigger:** `SessionStart`. Reads `package.json` (root, `apps/*`, `packages/*`), `pyproject.toml`, `requirements*.txt`, `go.mod`, `Cargo.toml` and marker folders (`prisma/`, `drizzle/`, `alembic/`, `eas.json`, `.claude/docs/`, `docs/tickets/`), then injects a short profile: `REPO PROFILE: Next.js, TypeScript, AI assistant, Prisma.` plus the skills to prefer (`/agent-feature` over `/feature`, `/db-change`, `/docs-sync` before the PR). Domain plugins are off at user scope (`install.sh`); an AI-assistant repo gets `agent@harness` enabled in its `.claude/settings.local.json`, from the next session, unless the repo set it `false`. No manifest → prints nothing. `CLAUDE_REPO_PROFILE=0` turns it off.

### `compact-advisor.sh` (core, always on)

**Trigger:** `Stop`. Context past 200k tokens (`CLAUDE_COMPACT_ADVISE_TOKENS`) → one line to the user suggesting `/compact`, repeated every 100k more. Never blocks; no tokens.

### `auto-decisions.sh` (dev, always on)

**Trigger:** `Stop`, in auto or bypass-permissions mode, on a ticket branch whose `plan.md` says `Risk: high`.

| Check | Action |
|-------|--------|
| No `## Auto decisions` section, or an entry without `challenged:` | BLOCK the stop once, with the format (`plugins/dev/references/auto-decisions.md`) |
| `- none: <why>` | allowed |

---

### `scope-gate.sh`

**Trigger:** `UserPromptSubmit` (every prompt)

Injects coordinator context into every implementation-intent prompt. Detects:
- Implementation words: add, implement, refactor, build, fix, change, etc.
- High-risk words: auth, login, jwt, payment, database, migration, schema, etc.

**Output:** JSON `additionalContext` block that activates the auto-coordinator with the appropriate lane hint. Non-blocking (exit 0 always).

---

### `blast-radius-check.sh`

**Trigger:** `PostToolUse(Edit|Write)`

Compares the edited file path against the `<files>` set declared in the active `specs/*/PLAN.md`. 

**If file is outside the plan's scope:**
- Default: WARN via JSON `additionalContext` ("blast-radius: edited X which is NOT in plan")
- Strict mode (`BLAST_RADIUS_STRICT=1`): BLOCK (exit 2)

Skips `specs/`, `docs/`, `*.md`, and `.claude/` files automatically.

---

### `risk-corroboration.sh`

**Trigger:** `PreToolUse(Bash)` on `git commit`

Cross-checks the staged diff against the Lane declared in `specs/*/SUMMARY.md`.

**Hard-gate categories it detects:**

| Category | Detection |
|----------|-----------|
| `high-blast` | Staged `settings.json` or any file under `hooks/` (project or plugin) |
| `data-loss/migration` | Files under `migrations/` or `alembic/`; `DROP TABLE`, `DELETE FROM`, `TRUNCATE`, `ALTER TABLE` in code |
| `external-provider` | `requirements.txt`, `package.json`, etc. staged; Stripe, Twilio, SendGrid, boto3, webhooks in code |
| `auth` | `login`, `session`, `jwt`, `password`, `oauth`, `bcrypt` in added lines |
| `authorization` | `role`, `permission`, `is_admin`, `rbac` in added lines |
| `audit/security` | `audit_log`, `encrypt`, `decrypt`, `pii` in added lines |
| `weakening-validation` | `assert`, `validator`, `required=True`, `raise` removed |

**Decision logic:**
- Lane is `high-risk` → allow (corroborated)
- Lane is `tiny` or `normal` → BLOCK (mismatch)
- No declared Lane → WARN (run `/coordinator`)

---

### `save-commit-memory.sh`

**Trigger:** `PostToolUse(Bash)` after `git commit`

**Input:** None (reads from git directly)

**Output:** Appends to `.claude/memory/commits/<YYYY-MM-DD>.md`:
```markdown
## `abc1234` — 2026-06-15T10:30:00

**feat: add CSV export**

- Author: Thang Ho Quang
- Branch: `feat/csv-export`
- Files:
  src/reports/export.ts
  src/reports/export.test.ts
```

Also updates `MEMORY.md` index and writes `memory/commits/last-sync.txt` (used by `sync-team.sh`).

Never blocks — all errors exit 0 silently.

---

### `state-breadcrumb.sh`

**Trigger:** `SessionEnd`

**Output:** Appends to `.claude/memory/sessions/<YYYY-MM-DD>.md`:
```markdown
### 2026-06-15T22:00:00 — <session-id>

- Last commit: `abc1234: feat: add CSV export`
- Branch: `feat/csv-export`
- Turns: 42
```

Also updates `MEMORY.md` index. Never blocks.

---

### `session-handoff.sh`

**Trigger:** `Stop` (session end)

**Output:** Writes `specs/HANDOFF.md` with:
- Branch name
- Last 8 commits (one-line)
- Git state (staged, unstaged, untracked files)
- Open specs (from `specs/*/SUMMARY.md`)
- Unresolved escalations (`decision: pending` entries)
- Prompt to fill in "What to do next"
- Warning if ≥5 files changed (suggests running `/compound`)

The next session reads and deletes this file automatically.

---

### `agent-progress.sh`

**Trigger:** `PostToolUse(Agent|Edit|Write|Bash)` and `PreToolUse(Agent)`

Prints colorized live progress to the terminal via `stderr` — shows which agent is running, which wave, and which tool calls are being made.

**Output format (stderr):**
```
10:30:15 [AGENT] architect → starting (wave 1)
10:30:22 [TOOL]  Edit src/components/Button.tsx
10:30:25 [AGENT] architect → done ✓
```

Non-blocking — exits 0 always. Purely cosmetic: helps track long multi-agent runs in real time.

---

### `headroom-compress.sh`

**Trigger:** `PostToolUse(Bash|Read)`

Checks the tool response length. If it exceeds `HEADROOM_WARN_THRESHOLD` (default: 8000 characters):
- Exits 2 with a system reminder asking Claude to call `headroom_compress`
- Claude then compresses the content and continues with a compact representation

If output is small: exits 0 silently (no overhead).

---

### `stacks/ruff-on-edit.sh`

**Trigger:** `PostToolUse(Edit)` on `.py` files (Python projects only)

Runs `ruff check --fix --silent` then `ruff format --silent` on the edited file. Never blocks.

---

### `stacks/eslint-on-edit.sh`

**Trigger:** `PostToolUse(Edit)` on `.ts`, `.tsx`, `.js`, `.jsx` files (TypeScript/JS projects only)

Runs `npx eslint --fix --quiet` if `.eslintrc*` or `eslint.config*` exists in the project root. Never blocks.

---

## Rules reference

Rules are Markdown files injected into agent prompts as governance constraints.

### Universal rules (`plugins/core/rules/`)

Installed to `~/.claude/rules/` by `scripts/install.sh` and loaded in every session:

| File | What it governs |
|------|----------------|
| `agent-principles.md` | Four hard rules: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution |
| `behavior.md` | Five core behaviors: think, simplify, surgical, goal-driven, communicate clearly |
| `orchestration.md` | Risk lanes (tiny/normal/high-risk), sub-agent rules, context budget, stopping conditions |
| `auto-correct-scope.md` | Rules 1–4 for when to auto-fix vs. require human confirmation |
| `wave-parallelism.md` | Wave invariants, dispatch rules, abort conditions, model selection |
| `plan-format.md` | XML task format for PLAN.md; required fields; when to create a plan |
| `git-workflow.md` | Commit format, branch naming, staging rules, PR rules, hard gates |
| `git.md` | Condensed git rules (project-level copy) |
| `testing.md` | Arrange→Act→Assert, what to test, mocking rules, coverage guidance |
| `security.md` | Secrets, auth/authz, input validation, code patterns to auto-escalate |
| `code-quality.md` | Guard clauses, DRY, naming, dead code, performance basics |
| `app-structure.md` | Fullstack folder ownership (features, components/ui, server/<aggregate>, db, lib, dev), size and naming; path-scoped to `src/**` |
| `api-contract.md` | Endpoint order (auth → validate → resource permission → service → DTO), error codes, 404 for another user's resource, additive contracts, test matrix |
| `data-access.md` | Owner-scoped repositories, parameterised queries, no N+1, transactions, migrations, real-engine tests |
| `typescript.md` | Strict mode, type safety, naming, async, error handling |
| `memory.md` | How to read/write the four memory types (user, feedback, project, reference) |

### Stack-specific rules (`plugins/core/templates/project/rules/stacks/`)

Copied to `.claude/rules/` only when the corresponding signal is detected during project initialization (`init.sh` or `/project-init`):

| File | Copied when | Key topics |
|------|------------|-----------|
| `stacks/typescript.md` | `typescript` signal | Strict mode, utility types, discriminated unions, `satisfies`, React+TS patterns |
| `stacks/javascript.md` | `nodejs` signal (or any JS project) | ES2020+ syntax, async patterns, naming, immutability, error handling |
| `stacks/react.md` | `react` signal | v19 APIs (`use`, `useOptimistic`, `useActionState`), Server/Client Components, hooks discipline, a11y |
| `stacks/jest.md` | `jest` signal | AAA structure, mocking (`jest.fn/spyOn/mock`), async testing, fake timers, factories |
| `stacks/python.md` | `python` signal | PEP8, type hints, async, error handling |
| `stacks/fastapi.md` | `fastapi` signal | Route patterns, Pydantic, dependency injection |
| `stacks/langgraph.md` | `langgraph` signal | Graph construction, state management, tool nodes |
| `stacks/nextjs.md` | `nextjs` signal | App Router, Server/Client Components, data fetching |

### Agent-specific rules (`plugins/agent/rules/`)

Read on-demand by AI assistant skills (`/agent-architect`, `/agent-feature`, `/agent-graph`, etc.):
- `agent-stock-first.md`: Prefer stock CopilotKit/LangGraph patterns before custom code
- `agent-identity-and-tools.md`: Tool identity, read vs mutation contracts
- `langgraph.md`: State management, graph topology, reducer rules
- `mastra.md`: Mastra registry, tools with request context, approval/suspend, workflows
- `agent-tracing-privacy.md`: PII sanitization in agent traces
- `agent-prompts.md`: Prompt engineering standards for agent nodes
- `agent-deps-pinning.md`: Exact package pinning for AI packages
- `agui-transport.md`: Agent-User Interaction transport standards

---

## Agents reference

Agent templates live in `plugins/core/templates/project/agents/` and are copied to `.claude/agents/` during project bootstrap. Each has YAML frontmatter controlling how Claude Code spawns them.

### `agents/architect.md`

| Field | Value |
|-------|-------|
| Model | `sonnet` |
| Mode | `bypassPermissions` |
| Max turns | 50 |
| Background | yes |
| Isolation | `worktree` (independent git worktree) |

**Role:** Design system components, evaluate trade-offs, produce implementation plans.

**Spawned by:** `/feature` (high-risk lane) when a design decision needs independent evaluation.

**Input:** Project goals, constraints from CLAUDE.md, existing architecture, the specific problem.

**Output:**
```markdown
## Approach: <name>
**Why this over alternatives:** ...
### Files to create / modify
### Public contract changes
### Plan (ordered atomic steps)
### Risks + mitigations
```

**Rule:** Does NOT write implementation code — produces plans only.

---

### `agents/reviewer.md`

**Role:** Code review focused on correctness, security, and convention compliance.

**Review checklist (in order):**
1. Correctness — logic errors, edge cases, null handling
2. Security — injection, auth gaps, secrets
3. Convention violations — naming, import order, layer boundaries
4. Test coverage — every changed behavior has a test
5. Simplicity — unnecessary abstraction, dead code

**Output format:** `file:line — severity (critical/major/minor) — finding — fix`

---

### `agents/qa.md`

**Role:** Quality assurance — verifies that changes work correctly before merge.

**Checklist:**
1. Run all commands in `specs/<slug>/SUMMARY.md` Verify table → confirm exit 0
2. Run full test suite
3. Run lint and type check
4. Trace the golden path manually
5. Check edge cases (empty, max, error paths)
6. Confirm all TEST_MATRIX.md planned rows are implemented

---

### `agents/pm-agent.md`

**Role:** Research phase — gathers codebase context before the architect runs.

**Spawned by:** `/ticket` workflow (first agent in the 5-agent pipeline).

**Steps:** Load `.claude/docs/`, read the ticket, identify affected modules/layers, find existing reusable code (file:line), check feature flags, identify risks.

**Output:** Research summary passed to `architect-agent` — affected areas, reuse opportunities, risks, open questions.

---

### `agents/implementer.md`

**Role:** Executes an approved plan precisely — no scope creep.

**Input:** Implementation plan from Planner/Architect + project conventions.

**Workflow:** Read task spec → read conventions → write failing test → implement → run lint/typecheck/tests → fill SUMMARY.md "What changed" + Verify table → update TEST_MATRIX.md → commit.

---

### `agents/developer-agent.md`

**Role:** Wave-based autonomous developer — breaks work into parallel waves and executes.

**Used for:** Complex multi-file tasks where independent subtasks can run in parallel.

**Model selection:** `sonnet` for complex logic, `haiku` for mechanical tasks (tests, types, simple CRUD).

---

### `agents/auto-dev.md`

**Role:** Fully autonomous developer — executes end-to-end without interruption.

| Field | Value |
|-------|-------|
| Model | `sonnet` |
| Mode | `bypassPermissions` |
| Max turns | 80 |

**Use when:** Task is well-defined and zero permission prompts are wanted.

**Workflow:** Plan (TaskCreate with waves) → implement each wave → verify → commit.

---

### `agents/verifier.md`

**Role:** Final verification before merge — reads SUMMARY.md Verify table and runs every check.

**Checklist:**
1. Run every command in `specs/<slug>/SUMMARY.md` Verify table → exit 0
2. Run lint, type check, tests
3. Confirm no debug statements (`console.log`, `debugger`, `pdb`) in staged files
4. Trace golden path manually
5. Check edge cases: empty, error, loading states
6. Confirm commit message matches project convention

**Output:** `PASS` or `FAIL` with evidence per check.

---

## Commands reference

Command templates live in `plugins/core/templates/project/commands/` and are copied to `.claude/commands/` during project bootstrap. Unlike skills (which have a `SKILL.md` wrapper with frontmatter), commands are raw prompt text loaded directly — lighter weight for simple workflows.

| Command | Invoke | What it does |
|---------|--------|-------------|
| `/ticket` | `/ticket #<issue> <description>` | Full 5-agent pipeline: PM → Architect → Wave Developer → Reviewer → QA |
| `/task` | `/task <description>` | Lightweight single-task: read conventions → implement → verify → commit |
| `/auto` | `/auto <description>` | Autonomous single-prompt dev: plan waves → execute → commit (no interruptions) |
| `/compact` | `/compact` | Summarize session → write HANDOFF.md → merge learnings into solutions/ |
| `/compound` | `/compound` | Crystallize session learnings → write to docs/solutions/ |

### `/ticket` pipeline detail

```
PM agent       → research ticket, find affected files, identify reuse
    ↓
Architect      → technical plan with wave-organized tasks
    ↓
Wave Developer → implement per plan (parallel waves where possible)
    ↓
Reviewer       → APPROVED or CHANGES REQUIRED (max 2 retry cycles)
    ↓
QA/Verifier    → lint + types + tests + golden path + commit
```

---

## Stack bundles reference

`plugins/core/stacks/` contains full workspace bundles (rules + skills) for specific project stacks. Unlike generic single-file rules, these bundles are tailored to a **specific project's real file paths, conventions, and tools**.

### When to use stack bundles vs stack rules

| | Stack rules (`rules/stacks/`) | Stack bundles (`stacks/`) |
|---|---|---|
| **Content** | Single `.md` rule file | Full bundle: `rules/` + `skills/` |
| **Scope** | Generic best practices | Project-specific conventions (real paths, team tools) |
| **Install** | `init.sh` copies per signal | Copy manually into `.claude/` for the specific project |
| **Example** | `react.md` — React best practices | `react-native/` — mobile monorepo workspace |

### `stacks/react-native/`

Complete workspace for a React Native monorepo project:
- Rules: `react-native.md`, `module-federation.md`, `rn-components.md`, `rn-screens.md`, `services.md`, `project-conventions.md`
- Skills: `/ticket`, `/task`, `/rn-component`, `/rn-testing`, `/rn-performance`, `/tanstack-query`, `/figma-to-screen`, `/gen-tests`, `/debug-runbook`, `/effect-services`, `/module-federation`, `/verify-feature`

### `stacks/nextjs/`

Next.js App Router rules: Server/Client Component boundaries, data fetching patterns, metadata API.

### `stacks/python/`

Python bundle: `python.md` (PEP8, type hints, async), `fastapi.md` (routes, Pydantic, DI), `langgraph.md` (graph construction, state management, tool nodes).

---

## Scripts reference

### `scripts/install.sh`

**Usage:** `bash scripts/install.sh`

One-command harness setup:
1. Backs up existing `~/.claude/CLAUDE.md`, `rules/`, `settings.json`, and replaced skills
2. Copies `global/CLAUDE.md` and `plugins/core/rules/` to `~/.claude/`
3. Registers local directory as marketplace `harness` and installs role plugins (`harness@harness`)
4. Migrates old skills out of `~/.claude/skills/` and drops duplicate hook registrations from `settings.json`

### `plugins/core/scripts/init.sh`

**Usage:** `bash plugins/core/scripts/init.sh [project-dir]` (or via `/project-init`)

Main project bootstrap script. Scans `src/` and generates the full `.claude/` harness.
- Lean mode (default): Shared skills/rules/hooks come from installed role plugins.
- Standalone mode (`STANDALONE=1`): Also copies shared rules, skills, commands, agents, and hooks into `.claude/`.

### `scripts/check.sh`

**Usage:** `bash scripts/check.sh`

Deterministic pre-commit checks:
1. Unit tests for lint-kit, skill progress, and compare shots
2. `lint-kit.py` validation (rules, dependencies, invariants)
3. `eval-triggers.py` skill trigger classifier evaluation
4. `claude plugin validate` on marketplace and all 10 plugins

### `scripts/eval-plugin.sh`

**Usage:** `bash scripts/eval-plugin.sh <plugin-name>`

Evaluates agent behavior on real test cases using an LLM judge. Supports `--runs <N>` and `--ablation with-without`.

### `scripts/setup-mcp.sh`

**Usage:** `bash scripts/setup-mcp.sh`

Sets up and registers recommended Model Context Protocol (MCP) servers.

### `scripts/setup-headroom.sh`

**Usage:** `bash scripts/setup-headroom.sh`

Installs headroom context compression:
1. Creates `~/.headroom-env` virtualenv
2. Installs `headroom-ai[all,mcp]`
3. Registers `headroom` MCP server at user scope for automatic tool output compression


---

### `TEST_MATRIX.template.md`

Tracks behavior coverage across test types. One row per behavior.

| Column | Values |
|--------|--------|
| `Behavior` | Description of expected behavior |
| `Contract` | yes / no (is this a public contract?) |
| `Unit` | yes / no |
| `Integration` | yes / no |
| `E2E` | yes / no |
| `Status` | planned → in_progress → implemented → changed → retired |
| `Evidence` | test path, Verify row reference, or commit sha |

Rule: Evidence cannot be `none` for `implemented` rows.

---

### `ESCALATIONS.template.md`

Records hard-gate decisions that require human input. Default: deny-on-no-response (unresolved entries block all dispatch).

Each entry (E001, E002, …) has:
- `raised_by`, `date`, `trigger`, `question`, `context`
- `options` (A/B choices with consequences)
- `default_if_no_response: BLOCK`
- `decision: pending` (or the decision once made)

---

### `settings.json.template`

Full permissions + deny list + hook registrations. Applied by `init.sh`.

**Allowed by default:** `Bash(*)`, `Read(*)`, `Edit(*)`, `Write(*)`, `WebFetch(*)`, `WebSearch(*)`

**Denied (always require user confirmation):**

| Command | Why |
|---------|-----|
| `rm -rf *`, `rm -r *` | Irreversible mass delete |
| `git push --force`, `git push -f` | Overwrites remote history |
| `git reset --hard` | Discards uncommitted work |
| `git clean -f` | Deletes untracked files |
| `git push * main`, `git push * master` | Direct push to protected branches |
| `git branch -D *` | Force-deletes branch |
| `kill -9 *`, `killall *` | Force-terminates processes |
| `npm publish`, `pnpm publish` | Releases to public registry |
| `sudo *` | Privilege escalation |
| `curl * \| bash`, `wget * \| bash` | Remote code execution |

---

## Memory system

Memory persists context across sessions. All memory files live in `.claude/memory/` and follow a frontmatter format:

```markdown
---
name: <slug>
description: <one-line summary>
metadata:
  type: user | feedback | project | reference
---

<content>
```

### Memory types

| Type | What it stores | When saved |
|------|---------------|-----------|
| `user` | Role, goals, preferences, knowledge level | When user profile details are learned |
| `feedback` | Corrections and validated approaches (both directions) | When user corrects Claude OR confirms a non-obvious approach worked |
| `project` | Active goals, decisions, deadlines | When project state changes |
| `reference` | Pointers to external resources (Linear, Grafana, etc.) | When external system locations are mentioned |

---

### Feedback memory — detailed

Feedback memory is the most important type: it prevents Claude from repeating the same mistakes and from drifting away from approaches the user has already validated.

**Two triggers — corrections AND confirmations:**

| Trigger | Example | Why save |
|---------|---------|---------|
| User corrects Claude | "don't mock the database in tests" | Prevents repeating the mistake |
| User confirms a non-obvious approach | "yes the single bundled PR was right" | Prevents over-cautious or wrong default next time |

Corrections are easy to notice. Confirmations are quieter — watch for the user accepting an unusual choice without pushback, or saying "yes exactly" / "perfect".

**File location:** `.claude/memory/feedback/<YYYY-MM-DD>.md` (one file per day, append)

**Required format — three parts:**

```markdown
---
name: feedback-<slug>
description: <one-line hook — specific enough to know when to apply this>
metadata:
  type: feedback
---

<The rule itself — lead with the behavior to adopt or avoid>

**Why:** <The reason the user gave — often a past incident or strong preference>
**How to apply:** <When and where this guidance kicks in; how to judge edge cases>

---

*Recorded: YYYY-MM-DD*
*Source: correction | confirmation*
```

The `Why:` line is critical — it lets Claude judge edge cases instead of blindly applying the rule.

**Examples:**

```markdown
---
name: feedback-no-db-mocks
description: Integration tests must hit a real database, never mocks
metadata:
  type: feedback
---

Never mock the database in integration tests — use a real local database.

**Why:** Prior incident where mock/prod divergence masked a broken migration. Tests passed, prod failed.
**How to apply:** For any test that exercises a database query or transaction. Unit tests on pure logic are fine to mock.

---
*Recorded: 2026-06-15*
*Source: correction*
```

```markdown
---
name: feedback-bundled-pr
description: For refactors in this area, prefer one bundled PR over many small ones
metadata:
  type: feedback
---

When refactoring shared infrastructure, ship as a single bundled PR — not split by file or layer.

**Why:** User confirmed this after I chose it: splitting would have been churn without benefit.
**How to apply:** When planning a multi-file refactor, default to one PR unless files are truly independent.

---
*Recorded: 2026-06-15*
*Source: confirmation*
```

**What NOT to save as feedback:**

- Code patterns, architecture, file paths — these are derivable from the code
- Debugging solutions or fix recipes — the fix is in the code; the commit message has context
- Anything already documented in `CLAUDE.md`
- Ephemeral task details or in-progress state

---

### Memory lifecycle

```
session starts
  ↓ MEMORY.md loaded into context (every session)
  ↓ specs/HANDOFF.md read if exists → deleted
  ↓
work happens
  ↓
git commit
  ↓ save-commit-memory.sh → .claude/memory/commits/YYYY-MM-DD.md
  ↓
session ends
  ↓ state-breadcrumb.sh → .claude/memory/sessions/YYYY-MM-DD.md
  ↓ session-handoff.sh → specs/HANDOFF.md
  ↓
user corrects Claude OR confirms non-obvious approach
  ↓ Claude saves feedback memory → .claude/memory/feedback/YYYY-MM-DD.md
  ↓
team project: next day
  ↓ /sync-memory → git pull + scan commits + flag overlaps
```

### Before acting on a memory

Memories reflect what was true when they were written — not necessarily now.

| Memory references | Verify before acting |
|---|---|
| A file path | `ls <path>` — the file may have moved or been deleted |
| A function or flag name | `grep -r <name> src/` — it may have been renamed |
| Repo state snapshot | Run `git log` — don't trust a stale activity summary |

If a memory conflicts with the current code → **trust the code**, then update or remove the stale memory.

### `MEMORY.md` index

Loaded into every session's context. Keep it under 200 lines (lines after 200 are truncated by Claude Code).

```markdown
# Memory Index

- [Title](path/to/file.md) — one-line hook explaining when this memory applies
```

Index maintenance rules:
- One entry per file, ≤150 characters per line
- Most recent date entries first
- Remove entries for memories older than ~30 days that no longer apply
- Do not write memory content into MEMORY.md — only pointers

---

## The coordinator flow

How all components work together for a typical feature request:

```
User: "add CSV export to the reports page"

1. scope-gate.sh fires
   → detects "add" (implementation intent)
   → no high-risk words
   → injects AUTO-COORDINATOR context with "Likely lane: tiny or normal"

2. Coordinator (auto-active) wakes up
   → Step 0: loads .claude/docs/ (architecture, conventions, stack, entry-points)
   → Step 1: loads docs/solutions/INDEX.md for prior learnings
   → Step 2: classifies → new-feature · Lane: normal · Confidence: 4/5

3. TaskCreate board created (all steps, before any work):
   #1 Planner: design CSV export approach
   #2 Implementer: build export endpoint + UI
   #3 Verifier: confirm export works

4. Specs initialized:
   → specs/add-csv-export/SUMMARY.md (Lane: normal, Confidence: high)
   → specs/add-csv-export/TEST_MATRIX.md (planned rows)
   → specs/add-csv-export/ESCALATIONS.md (empty)

5. Wave 1: Planner (sonnet)
   → reads docs, finds relevant files
   → writes PLAN.md with wave-organized tasks

6. Wave 2: Implementer (sonnet)
   → follows PLAN.md precisely
   → writes code, writes tests
   → fills SUMMARY.md "What changed" + "Verify" table

7. Commit: git commit
   → commit-quality-gate.sh: no secrets, no debug artifacts → ALLOW
   → risk-corroboration.sh: Lane=normal, no hard-gate signals → ALLOW
   → save-commit-memory.sh: writes to memory/commits/ → ALLOW

8. Wave 3: Verifier (sonnet)
   → runs every command in SUMMARY.md Verify table
   → reports PASS

9. Session end (Stop hook):
   → session-handoff.sh writes specs/HANDOFF.md
   → state-breadcrumb.sh appends to memory/sessions/

10. Next session:
    → reads HANDOFF.md → deletes it → continues from "Next steps"
```

---

## Risk lanes & hard gates

### Lanes

| Lane | Criteria | Process |
|------|----------|---------|
| `tiny` | Single file, no external contracts, reversible, <30 min | Direct edit; hooks are safety net |
| `normal` | Multi-file, internal API changes, moderate complexity | Research brief + plan before coding |
| `high-risk` | Auth, migration, public contract, payment, security, `.claude/` | Full chain: research → plan → confirm → build → review |

### Hard gates (always `high-risk`, cannot self-downgrade)

Any of these forces `high-risk` regardless of scope:
- Authentication / authorization
- Data loss / schema migration
- Audit / security controls
- External provider behavior (Stripe, Twilio, SendGrid, AWS)
- Public API contract changes (adding/removing/renaming fields)
- Removing or weakening validation
- Touching `.claude/` config files or hooks
- Multi-domain changes

### Stopping rules

The coordinator stops and asks the human when:
- Confidence drops below medium
- A hard gate is discovered mid-task
- Scope needs to expand beyond the plan
- An unresolved `ESCALATIONS.md` entry exists (`decision: pending`)
- Verifier fails twice in a row
- A teammate's recent commit conflicts with the planned approach

---

## Dynamic workflows

Dynamic workflows are a Claude Code native feature (v2.1.154+) for orchestrating **dozens to hundreds of subagents** from a JavaScript script Claude writes. The harness integrates them at two levels: the coordinator's scale-check and the `/workflow` command.

### When to use

| Use a dynamic workflow | Use in-context wave agents |
|------------------------|----------------------------|
| 10+ files changed independently | < 8 files |
| Codebase-wide audit or migration | Changes in 1–2 modules |
| Adversarial cross-check of results | Single linear pipeline |
| Orchestration worth saving/rerunning | One-off in-session task |

### Trigger

```text
ultracode: audit every API endpoint under src/routes/ for missing auth checks
```

Or naturally: "use a workflow for this migration", "run a workflow".
Or for the whole session: `/effort ultracode`

### Harness command

```text
/workflow <task description>
```

Guides you through the decision (workflow vs. waves), triggers the correct path, and explains the save/reuse flow.

### Built-in workflows

| Command | What it does |
|---------|-------------|
| `/deep-research <question>` | Fan-out web research → cross-check sources → adversarial vote → cited report |

### Save for reuse

After a run: `/workflows` → select run → `s`

| Save path | Scope |
|-----------|-------|
| `.claude/workflows/<name>.js` | Project — shared with team via git |
| `~/.claude/workflows/<name>.js` | Personal — all projects |

Saved workflows become `/<name>` slash commands.

### Limits

| Constraint | Value |
|-----------|-------|
| Concurrent agents | 16 max |
| Total per run | 1,000 max |
| Resumable | Within same session only |
| Mid-run input | Not supported |

### Disable

```json
{ "disableWorkflows": true }
```

or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`.

---

## Extending the harness

### Add a new skill

```bash
mkdir -p plugins/<plugin>/skills/<name>
cat > plugins/<plugin>/skills/<name>/SKILL.md << 'EOF'
---
name: <name>
description: <trigger condition — when to invoke this>
model: sonnet | haiku
effort: high | medium | low
---

# <Name>

**Invoke:** `/<name> [args]`

## Step 1 — ...
## Step 2 — ...
EOF

bash scripts/check.sh   # lint + trigger eval + validate; a local install loads it at the next session
```

The `description` field is used by Claude Code to auto-invoke the skill. Make it a specific, actionable trigger phrase.

### Add a new rule

```bash
cat > plugins/core/rules/<name>.md << 'EOF'
# <Name> Rules

## Rule 1
<imperative instruction>

## Rule 2
<imperative instruction>
EOF

# Install to ~/.claude/rules/ for all future sessions:
bash scripts/install.sh
```

Rules must be imperative ("do X", "never Y") — not descriptive. Add `paths:` frontmatter if the rule applies only to specific file patterns.

### Add a new hook

```bash
cat > plugins/guards/hooks/<name>.sh << 'EOF'
#!/bin/bash
# <name>.sh — <description>
# Trigger: <PreToolUse|PostToolUse|UserPromptSubmit|Stop>(<matcher>)
# Exit 2 to block, 0 to allow

INPUT=$(cat /dev/stdin)
# ... your logic ...

exit 0
EOF

chmod +x plugins/guards/hooks/<name>.sh

# Register in plugins/guards/hooks/hooks.json under the appropriate event
# Use "${CLAUDE_PLUGIN_ROOT}"/hooks/<name>.sh as the command path
```

Hook exit codes: `0` = allow, `2` = block. Never exit `1` (reserved for errors).

### Add a stack-specific rule

```bash
cat > plugins/core/templates/project/rules/stacks/<name>.md << 'EOF'
# <Stack Name> Rules
...
EOF

# Add detection in plugins/core/scripts/init.sh:
has_signal "<name>" && cp "$TEMPLATES/rules/stacks/<name>.md" "$CLAUDE_DIR/rules/<name>.md" || true
```

### Update an existing project after harness changes

```bash
# Re-run project initialization (warns before overwriting existing settings.json):
bash plugins/core/scripts/init.sh /path/to/project
# or in Claude Code within the project:
/project-init
```
