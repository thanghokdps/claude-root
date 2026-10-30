# Plugins

The kit is one marketplace, `harness`, with one plugin per role. Install the role you are and its dependencies come with it:

```text
/plugin marketplace add thanghokdps/claude-root     # or the GitLab URL in the root README
/plugin install dev@harness                         # one role
/plugin install harness@harness                     # the eight general role plugins
```

| Plugin | Role | Skills | Hooks | Depends on |
|---|---|---|---|---|
| [`progress`](progress/README.md) | A skill's checklist and live ✅ progress; never blocks | — | `skill-progress` | — |
| [`core`](core/README.md) | Session and project basics every role uses | `verify-done` `project-init` `docs-sync` `compact` `compound` `sync-memory` `btw` | `branch-guard` `secret-guard` `sensitive-path` `edit-guard` `step-limit` `repo-profile` `compact-advisor` `learn-capture` | progress |
| [`plan`](plan/README.md) | Analyse, split, estimate and design before code | `breakdown` `kickoff` `brainstorming` `grill` `domain-model` `codebase-design` `writing-plans` | — | progress |
| [`review`](review/README.md) | Review a diff, a PR or a whole repo | `review-checklist` `review-diff` `blast-radius` `create-pr` `resolve-pr-feedback` `debt-ledger` `repo-audit` | — | progress |
| [`dev`](dev/README.md) | Build and fix for every role; `/feature` dispatches slices to the role packs | `coordinator` `feature` `ticket` `fix-bug` `tdd` `resolve-question` `checkpoint` | `ticket-ledger` `ticket-gate` `test-lock` `weakened-check` `auto-decisions` | core, plan, review, ship |
| [`frontend`](frontend/README.md) | Role pack: web UI, enabled per repo | `ui-feature` `design-ui` + agent `frontend-engineer` | — | progress, dev |
| [`backend`](backend/README.md) | Role pack: server side, enabled per repo | `api-endpoint` `db-change` `api-client` + agent `backend-engineer` | — | progress, dev |
| [`ship`](ship/README.md) | Land and release | `finish-branch` `ci-triage` `release-checklist` `write-migration` `incident` `sync-remote` | `release-gate` `infra-gate` | core |
| [`mobile`](mobile/README.md) | Role pack: React Native / Expo screens, enabled per repo | `mobile-feature` + agent `mobile-engineer` | — | progress, dev |
| [`devops`](devops/README.md) | Role pack: CI/CD, containers, infrastructure, enabled per repo | `pipeline` `container` `infra-change` + agent `devops-engineer` | — (`infra-gate` is in ship) | progress, dev |
| [`ai`](ai/README.md) | Role pack: AI assistants on CopilotKit · AG-UI with Mastra, LangChainJS or LangGraph, enabled per repo | `agent-architect` `agent-feature` `agent-tool` `agent-hitl` `agent-graph` `agent-frontend` `agent-design-ui` `agent-rag` `agent-evals` `agent-verify-turn` `agent-security` `agent-prompt-review` + agent `ai-engineer` | — | progress, dev |
| [`workplace`](workplace/README.md) | Domain pack for HR / workplace apps, enabled per repo | `workplace-review` | — | progress |
| [`lead`](lead/README.md) | Improve the process | `retro` `diagnose-session` `writing-skills` | — | core |
| [`guards`](guards/README.md) | Opt-in guard-rail hooks | — | `commit-quality-gate` `risk-corroboration` `push-evidence` `scope-gate` `blast-radius-check` `format-on-edit` `run-log` `headroom-compress` `session-handoff` `session-resume` `state-breadcrumb` `notify-on-finish` | dev |
| [`harness`](harness/README.md) | Bundle of the eight general role plugins | — | — | core, plan, review, dev, ship, lead, guards, progress |

Each skill is a Markdown prompt program in `plugins/<plugin>/skills/<name>/SKILL.md`, invoked as `/<name>` (or `/<plugin>:<name>` when two plugins define the same name). Skills fire on their own from what you type; the slash command is optional. Each plugin's README has the skill table with when to use it and an example prompt.

## Which skill for which job

| I want to… | Skill | Plugin |
|---|---|---|
| Start a project from the documents we have | `/kickoff` → `/writing-plans` | plan |
| Turn a requirement or epic into tracker tasks with estimates | `/breakdown` → `/ticket <id>` per task | plan → dev |
| Design a feature before building it | `/brainstorming` → `/grill` → `/writing-plans` | plan |
| Build a feature, or work a ticket by id | just describe it · `/feature` · `/ticket <id>` | dev |
| Fix a bug that keeps coming back | `/fix-bug` (locks the reproducing test) | dev |
| Add an endpoint · a table · a third-party API client | `/api-endpoint` · `/db-change` · `/api-client` | backend |
| Add a React screen · a React Native screen | `/ui-feature` · `/mobile-feature` | frontend · mobile |
| Add a CI job · a Dockerfile · a Terraform / k8s / Helm change | `/pipeline` · `/container` · `/infra-change` | devops |
| Match a Figma design | `/design-ui` (any page) · `/agent-design-ui` (the chat) | frontend · ai |
| Prove the work is done | `/verify-done` · `/checkpoint` | core · dev |
| Review before the PR, then answer the review | `/review-checklist` · `/blast-radius` · `/resolve-pr-feedback` | review |
| Land the branch, read a red build, cut a release | `/finish-branch` · `/ci-triage` · `/release-checklist` | ship |
| Change the schema safely | `/write-migration` (always high-risk) | ship |
| Run an incident | `/incident` | ship |
| Keep the project's docs and memory current | `/docs-sync` · `/compact` · `/compound` · `/sync-memory` | core |
| Start, grow, test and secure an AI assistant | `/agent-architect` → `/agent-feature` → `/agent-verify-turn` → `/agent-evals` → `/agent-security` | ai |
| Look back at the week or at a bad session | `/retro` · `/diagnose-session` | lead |

## How the skills hand off

```text
intake   requirement → /breakdown → tasks with criteria and estimates on the tracker → /ticket <id> each
design   /kickoff or /brainstorming → design.md → /grill → /writing-plans → PLAN.md (a verify command per task)
build    PLAN.md → /feature dispatches each slice to its pack's engineer (backend: api-endpoint, db-change, api-client · frontend: ui-feature, design-ui · mobile: mobile-feature · devops: pipeline, container, infra-change · ai: agent-*) → /checkpoint
prove    /verify-done → /review-checklist (+ /blast-radius on shared code) → /docs-sync → /finish-branch
agent    /agent-architect → ADR + scaffold → /agent-feature → agent-tool · agent-hitl · agent-graph · agent-frontend → /agent-verify-turn → /agent-evals → /agent-security
end      /compact (handoff for the next session) · /compound (lessons to docs/solutions/)
```

## Adding a skill

Read [`/writing-skills`](lead/skills/writing-skills/SKILL.md) first. Then:

1. Create `plugins/<plugin>/skills/<name>/SKILL.md`; `name` must match the directory. Pick the plugin by role.
2. Add `eval/triggers/<name>.json`: three prompts that must rank it in the top 3, one or two owned by a neighbour.
3. A step that runs another plugin's skill needs that plugin in `dependencies` (`plugin.json`); a mention only says "(<plugin>, if installed)".
4. Add the row to that plugin's README and to the table above, then `bash scripts/check.sh`.
