# Plugins

The kit is a marketplace of role plugins. Install one role and its dependencies come with it:

```
/plugin marketplace add thanghokdps/claude-root
/plugin install agent@harness      # one role
/plugin install harness@harness        # everything
```

| Plugin | Role | Depends on |
|--------|------|-----------|
| `progress` | Skill checklist + live ✅ progress (hooks only, never blocks) | — |
| `core` | Session + project basics every role uses | progress |
| `plan` | Architect / tech lead: design before code | progress |
| `review` | Reviewer: diffs, PRs, impact | progress |
| `dev` | Developer: build, fix, test-first | core, plan, review |
| `ship` | Release / CI owner | core |
| `agent` | AI-agent engineer (CopilotKit, LangGraph) | progress, dev, ship |
| `lead` | Process owner: retro, session diagnosis, skill authoring | core |
| `guards` | Personal guard-rail hooks (opt-in) | dev |
| `harness` | Bundle | all nine |

Each skill is a Markdown prompt program invoked via `/skill-name` (or `/<plugin>:<skill-name>`) in Claude Code.

| Skill | Plugin | Command | Purpose | Lanes |
|-------|--------|---------|---------|-------|
| [feature](dev/skills/feature/SKILL.md) | `dev` | `/feature <desc>` | Risk intake → plan → build → review | tiny/normal/high |
| [fix-bug](dev/skills/fix-bug/SKILL.md) | `dev` | `/fix-bug <symptom>` | Tight red loop → minimise → hypothesise → fix → regression test | tiny/normal |
| [review-checklist](review/skills/review-checklist/SKILL.md) | `review` | `/review-checklist [PR]` | correctness → tests → scale → readability → security → scope; numbered findings, each with a failing case | n/a |
| [debt-ledger](review/skills/debt-ledger/SKILL.md) | `review` | `/debt-ledger [marker]` | Every `shortcut:` comment → limit + upgrade trigger; flags `no-trigger` | n/a |
| [ci-triage](ship/skills/ci-triage/SKILL.md) | `ship` | `/ci-triage [run]` | Red build → regression / flaky / environment + one-sentence root cause | n/a |
| [release-checklist](ship/skills/release-checklist/SKILL.md) | `ship` | `/release-checklist <version>` | Scope → gates → migrations → notes → tag → deploy → smoke → rollback | high |
| [write-migration](ship/skills/write-migration/SKILL.md) | `ship` | `/write-migration <change>` | Expand/contract, reversible, batched backfill, tested down path | high |
| [verify-done](core/skills/verify-done/SKILL.md) | `core` | `/verify-done` | Fresh evidence for the "done when" check before claiming completion | all |
| [finish-branch](ship/skills/finish-branch/SKILL.md) | `ship` | `/finish-branch` | Verify → PR/MR, merge, keep or discard → clean up worktree | n/a |
| [sync-remote](ship/skills/sync-remote/SKILL.md) | `ship` | `/sync-remote [repo-dir …]` | GitHub ↔ GitLab: fast-forward branches and missing tags; main, env branches and diverged refs left to you | medium |
| [diagnose-session](lead/skills/diagnose-session/SKILL.md) | `lead` | `/diagnose-session [id]` | Transcript evidence for misfires, ignored plans, noisy hooks → kit fix | n/a |
| [retro](lead/skills/retro/SKILL.md) | `lead` | `/retro [since]` | Weekly retro from commits/PRs/CI → ≤3 things to standardize | n/a |
| [checkpoint](dev/skills/checkpoint/SKILL.md) | `dev` | `/checkpoint` | Progress vs plan + all quality gates | n/a |
| [sync-memory](core/skills/sync-memory/SKILL.md) | `core` | `/sync-memory` | Pull latest + rebuild memory from your commits | n/a |
| [brainstorming](plan/skills/brainstorming/SKILL.md) | `plan` | `/brainstorming` | Rough idea → `specs/<slug>/design.md` | normal/high |
| [grill](plan/skills/grill/SKILL.md) | `plan` | `/grill [target]` | Adversarial one-question-at-a-time interview that hardens a design | normal/high |
| [writing-plans](plan/skills/writing-plans/SKILL.md) | `plan` | `/writing-plans` | Approved design → wave-organized `PLAN.md` | normal/high |
| [domain-model](plan/skills/domain-model/SKILL.md) | `plan` | `/domain-model` | Ubiquitous language → `.claude/docs/glossary.md` + ADRs | normal/high |
| [design-ui](dev/skills/design-ui/SKILL.md) | `dev` | `/design-ui <figma\|folder>` | Design → UI: states, tokens, primitives from the UI library, screenshot diff incl. narrow widths | normal |
| [resolve-question](dev/skills/resolve-question/SKILL.md) | `dev` | `/resolve-question <q>` | Fact → `file:line` citation; choice → asked as options. Fewer questions to the user | all |
| [tdd](dev/skills/tdd/SKILL.md) | `dev` | `/tdd` | Red → green loop, one seam and one slice per cycle | all |
| [codebase-design](plan/skills/codebase-design/SKILL.md) | `plan` | `/codebase-design` | Deep-module vocabulary — depth, seam, leverage, locality | reference |
| [writing-skills](lead/skills/writing-skills/SKILL.md) | `lead` | `/writing-skills` | How to author and prune skills in this harness | reference |
| [coordinator](dev/skills/coordinator/SKILL.md) | `dev` | `/coordinator <req>` | Classify intent → lane → dispatch. The router | all |
| [project-init](core/skills/project-init/SKILL.md) | `core` | `/project-init` | Full `.claude/` bootstrap — docs, agents, hooks, rules | all |
| [review-diff](review/skills/review-diff/SKILL.md) | `review` | `/review-diff` | Diff walkthrough with Mermaid architecture diagrams | n/a |
| [blast-radius](review/skills/blast-radius/SKILL.md) | `review` | `/blast-radius` | Change impact before merge: callers, consumers, contracts, untested paths, rollback plan | n/a |
| [create-pr](review/skills/create-pr/SKILL.md) | `review` | `/create-pr` | Branch diff → PR description | n/a |
| [resolve-pr-feedback](review/skills/resolve-pr-feedback/SKILL.md) | `review` | `/resolve-pr-feedback [PR]` | Every open review thread: fix, answer or decline, one push, a reply on each | n/a |
| [verify-feature](core/stacks/react-native/skills/verify-feature/SKILL.md) | `core` stacks/react-native (copied by init.sh) | `/verify-feature` | Lint + typecheck + tests across affected workspaces | n/a |
| [gen-tests](core/stacks/react-native/skills/gen-tests/SKILL.md) | `core` stacks/react-native (copied by init.sh) | `/gen-tests <path>` | Scaffold tests for code that already exists | n/a |
| [compact](core/skills/compact/SKILL.md) | `core` | `/compact` | Summarize session → HANDOFF.md + memory | n/a |
| [compound](core/skills/compound/SKILL.md) | `core` | `/compound` | Crystallize session learnings → `docs/solutions/` | n/a |
| [btw](core/skills/btw/SKILL.md) | `core` | `/btw <question>` | Quick lookup mid-task, no tasks or side effects | n/a |
| [figma-to-screen](core/stacks/react-native/skills/figma-to-screen/SKILL.md) | `core` stacks/react-native (copied by init.sh) | `/figma-to-screen` | Figma frame → screen implementation | normal |
| [agent-architect](agent/skills/agent-architect/SKILL.md) | `agent` | `/agent-architect [greenfield\|skeleton\|audit]` | AI assistant architecture: one-question interview → ADR → scaffold, an empty skeleton on a named stack, or stock-vs-custom audit | normal/high |
| [agent-feature](agent/skills/agent-feature/SKILL.md) | `agent` | `/agent-feature <capability>` | Feature in an existing assistant: ADR fit check, reuse inventory, reuse/extend/new per slice, duplicate check | normal |
| [agent-design-ui](agent/skills/agent-design-ui/SKILL.md) | `agent` | `/agent-design-ui <figma\|folder>` | `/design-ui` + chat states, CopilotKit theme, ladder per chat element | normal |
| [agent-tool](agent/skills/agent-tool/SKILL.md) | `agent` | `/agent-tool <tool>` | Agent tool: trusted identity, read vs mutation, retry/audit, short description, test | normal |
| [agent-hitl](agent/skills/agent-hitl/SKILL.md) | `agent` | `/agent-hitl <write>` | Mutation behind interrupt: target resolution, pending action, confirm/cancel/replay, client render | normal/high |
| [agent-graph](agent/skills/agent-graph/SKILL.md) | `agent` | `/agent-graph <scope>` | Agents, router, handoff, boundary rules, prompts, middleware order | normal |
| [agent-frontend](agent/skills/agent-frontend/SKILL.md) | `agent` | `/agent-frontend <change>` | CopilotKit v2 React: provider headers, context, tool renderers, aimock e2e | normal |
| [agent-verify-turn](agent/skills/agent-verify-turn/SKILL.md) | `agent` | `/agent-verify-turn [local\|prod-trace]` | Real turn + AG-UI stream as evidence; classify a production trace before fixing | all |
| [agent-evals](agent/skills/agent-evals/SKILL.md) | `agent` | `/agent-evals [unit\|dataset\|suite\|observability\|compare-models]` | Fake-model unit tests, JSONL eval dataset, judged suite with baseline gate, tracing setup, model comparison | normal |
| [agent-security](agent/skills/agent-security/SKILL.md) | `agent` | `/agent-security [scope]` | Agent threat model: injection, confused deputy, exfiltration, trace PII, compliance mapping | high |
| [agent-prompt-review](agent/skills/agent-prompt-review/SKILL.md) | `agent` | `/agent-prompt-review [path\|diff]` | Prompt, tool-description and output-schema diff read as the model reads it, with an eval per must-fix | normal |

## Skill handoff map

Design chain — run before building anything non-trivial:

```
/brainstorming → design.md
    ↓          ↕ /domain-model → glossary.md + ADRs (runs alongside)
/grill → hardens design.md · unresolved findings → ESCALATIONS.md (blocks dispatch)
    ↓
/writing-plans → PLAN.md (each task carries a <verify> command)
    ↓
/tdd → the <verify> command is the red → green target
```

Two reference skills carry vocabulary rather than stages: `/codebase-design` (how a module should be shaped) and `/writing-skills` (how a skill should be written).

Build chain:

```
/project-init
    ↓ (first run)
/feature → risk intake → tiny: direct | normal: plan + build | high: research + plan + confirm + build
    ↓
/checkpoint → quality gates → ✅ continue or ❌ fix
    ↓
/review-checklist → findings → fix → /checkpoint again (risky: /code-review ultra)
    ↓ (team project, start of session)
/sync-memory → pull latest → memory updated → ready to work
```

## Adding a new skill

Read [`/writing-skills`](lead/skills/writing-skills/SKILL.md) first — it owns the how (invocation choice, information hierarchy, pruning, failure modes). The checklist:

1. Create `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter; `name` must match the directory. Pick the plugin by role.
2. Decide invocation. Model-invoked pays context load every turn — pick it only when the agent or another skill must reach the skill unprompted. Otherwise `disable-model-invocation: true`.
3. Add the row to this README table and place it in the right chain.
4. A step that runs another plugin's skill needs that plugin in `dependencies` (plugin.json); a mention only says "(<plugin>, if installed)". `bash scripts/check.sh` enforces both.
5. Only add to the `for entry in …` loop in `plugins/core/scripts/init.sh` if a project needs its own copy.
