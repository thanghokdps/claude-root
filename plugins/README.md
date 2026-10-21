# Plugins

The kit is a marketplace of role plugins. Install one role and its dependencies come with it:

```
/plugin marketplace add thanghokdps/claude-root
/plugin install thang-agent@thang-kit      # one role
/plugin install thang-kit@thang-kit        # everything
```

| Plugin | Role | Depends on |
|--------|------|-----------|
| `thang-progress` | Skill checklist + live ✅ progress (hooks only, never blocks) | — |
| `thang-core` | Session + project basics every role uses | progress |
| `thang-plan` | Architect / tech lead: design before code | progress |
| `thang-review` | Reviewer: diffs, PRs, impact | progress |
| `thang-dev` | Developer: build, fix, test-first | core, plan, review |
| `thang-ship` | Release / CI owner | core |
| `thang-agent` | AI-agent engineer (CopilotKit, LangGraph) | progress |
| `thang-lead` | Process owner: retro, session diagnosis, skill authoring | core |
| `thang-guards` | Personal guard-rail hooks (opt-in) | dev |
| `thang-kit` | Bundle | all nine |

Each skill is a Markdown prompt program invoked via `/skill-name` (or `/<plugin>:<skill-name>`) in Claude Code.

| Skill | Plugin | Command | Purpose | Lanes |
|-------|--------|---------|---------|-------|
| [init-project](thang-core/skills/init-project/SKILL.md) | `thang-core` | `/init-project` | Scan src → generate .claude/ harness | all |
| [feature](thang-dev/skills/feature/SKILL.md) | `thang-dev` | `/feature <desc>` | Risk intake → plan → build → review | tiny/normal/high |
| [fix-bug](thang-dev/skills/fix-bug/SKILL.md) | `thang-dev` | `/fix-bug <symptom>` | Tight red loop → minimise → hypothesise → fix → regression test | tiny/normal |
| [review-checklist](thang-review/skills/review-checklist/SKILL.md) | `thang-review` | `/review-checklist [PR]` | correctness → tests → readability → security → scope; ≥3 actionable comments | n/a |
| [ci-triage](thang-ship/skills/ci-triage/SKILL.md) | `thang-ship` | `/ci-triage [run]` | Red build → regression / flaky / environment + one-sentence root cause | n/a |
| [release-checklist](thang-ship/skills/release-checklist/SKILL.md) | `thang-ship` | `/release-checklist <version>` | Scope → gates → migrations → notes → tag → deploy → smoke → rollback | high |
| [write-migration](thang-ship/skills/write-migration/SKILL.md) | `thang-ship` | `/write-migration <change>` | Expand/contract, reversible, batched backfill, tested down path | high |
| [verify-done](thang-core/skills/verify-done/SKILL.md) | `thang-core` | `/verify-done` | Fresh evidence for the "done when" check before claiming completion | all |
| [finish-branch](thang-ship/skills/finish-branch/SKILL.md) | `thang-ship` | `/finish-branch` | Verify → PR/MR, merge, keep or discard → clean up worktree | n/a |
| [diagnose-session](thang-lead/skills/diagnose-session/SKILL.md) | `thang-lead` | `/diagnose-session [id]` | Transcript evidence for misfires, ignored plans, noisy hooks → kit fix | n/a |
| [retro](thang-lead/skills/retro/SKILL.md) | `thang-lead` | `/retro [since]` | Weekly retro from commits/PRs/CI → ≤3 things to standardize | n/a |
| [checkpoint](thang-dev/skills/checkpoint/SKILL.md) | `thang-dev` | `/checkpoint` | Progress vs plan + all quality gates | n/a |
| [sync-memory](thang-core/skills/sync-memory/SKILL.md) | `thang-core` | `/sync-memory` | Pull latest + rebuild memory from your commits | n/a |
| [brainstorming](thang-plan/skills/brainstorming/SKILL.md) | `thang-plan` | `/brainstorming` | Rough idea → `specs/<slug>/design.md` | normal/high |
| [grill](thang-plan/skills/grill/SKILL.md) | `thang-plan` | `/grill [target]` | Adversarial one-question-at-a-time interview that hardens a design | normal/high |
| [writing-plans](thang-plan/skills/writing-plans/SKILL.md) | `thang-plan` | `/writing-plans` | Approved design → wave-organized `PLAN.md` | normal/high |
| [domain-model](thang-plan/skills/domain-model/SKILL.md) | `thang-plan` | `/domain-model` | Ubiquitous language → `.claude/docs/glossary.md` + ADRs | normal/high |
| [tdd](thang-dev/skills/tdd/SKILL.md) | `thang-dev` | `/tdd` | Red → green loop, one seam and one slice per cycle | all |
| [codebase-design](thang-plan/skills/codebase-design/SKILL.md) | `thang-plan` | `/codebase-design` | Deep-module vocabulary — depth, seam, leverage, locality | reference |
| [writing-skills](thang-lead/skills/writing-skills/SKILL.md) | `thang-lead` | `/writing-skills` | How to author and prune skills in this harness | reference |
| [coordinator](thang-dev/skills/coordinator/SKILL.md) | `thang-dev` | `/coordinator <req>` | Classify intent → lane → dispatch. The router | all |
| [project-init](thang-core/skills/project-init/SKILL.md) | `thang-core` | `/project-init` | Full `.claude/` bootstrap — docs, agents, hooks, rules | all |
| [review-diff](thang-review/skills/review-diff/SKILL.md) | `thang-review` | `/review-diff` | Diff walkthrough with Mermaid architecture diagrams | n/a |
| [create-pr](thang-review/skills/create-pr/SKILL.md) | `thang-review` | `/create-pr` | Branch diff → PR description | n/a |
| [verify-feature](thang-core/stacks/react-native/skills/verify-feature/SKILL.md) | `thang-core` stacks/react-native (copied by init.sh) | `/verify-feature` | Lint + typecheck + tests across affected workspaces | n/a |
| [gen-tests](thang-core/stacks/react-native/skills/gen-tests/SKILL.md) | `thang-core` stacks/react-native (copied by init.sh) | `/gen-tests <path>` | Scaffold tests for code that already exists | n/a |
| [compact](thang-core/skills/compact/SKILL.md) | `thang-core` | `/compact` | Summarize session → HANDOFF.md + memory | n/a |
| [compound](thang-core/skills/compound/SKILL.md) | `thang-core` | `/compound` | Crystallize session learnings → `docs/solutions/` | n/a |
| [btw](thang-core/skills/btw/SKILL.md) | `thang-core` | `/btw <question>` | Quick lookup mid-task, no tasks or side effects | n/a |
| [figma-to-screen](thang-core/stacks/react-native/skills/figma-to-screen/SKILL.md) | `thang-core` stacks/react-native (copied by init.sh) | `/figma-to-screen` | Figma frame → screen implementation | normal |
| [agent-architect](thang-agent/skills/agent-architect/SKILL.md) | `thang-agent` | `/agent-architect [greenfield\|audit]` | AI assistant architecture: one-question interview → ADR → scaffold, or stock-vs-custom audit | normal/high |
| [agent-tool](thang-agent/skills/agent-tool/SKILL.md) | `thang-agent` | `/agent-tool <tool>` | Agent tool: trusted identity, read vs mutation, retry/audit, short description, test | normal |
| [agent-hitl](thang-agent/skills/agent-hitl/SKILL.md) | `thang-agent` | `/agent-hitl <write>` | Mutation behind interrupt: target resolution, pending action, confirm/cancel/replay, client render | normal/high |
| [agent-graph](thang-agent/skills/agent-graph/SKILL.md) | `thang-agent` | `/agent-graph <scope>` | Agents, router, handoff, boundary rules, prompts, middleware order | normal |
| [agent-frontend](thang-agent/skills/agent-frontend/SKILL.md) | `thang-agent` | `/agent-frontend <change>` | CopilotKit v2 React: provider headers, context, tool renderers, aimock e2e | normal |
| [agent-verify-turn](thang-agent/skills/agent-verify-turn/SKILL.md) | `thang-agent` | `/agent-verify-turn [local\|prod-trace]` | Real turn + AG-UI stream as evidence; classify a production trace before fixing | all |
| [agent-evals](thang-agent/skills/agent-evals/SKILL.md) | `thang-agent` | `/agent-evals [unit\|suite\|compare-models]` | Fake-model unit tests, judged eval suite with baseline gate, model comparison | normal |
| [agent-security](thang-agent/skills/agent-security/SKILL.md) | `thang-agent` | `/agent-security [scope]` | Agent threat model: injection, confused deputy, exfiltration, trace PII, compliance mapping | high |

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
/init-project
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

Read [`/writing-skills`](thang-lead/skills/writing-skills/SKILL.md) first — it owns the how (invocation choice, information hierarchy, pruning, failure modes). The checklist:

1. Create `plugins/<plugin>/skills/<name>/SKILL.md` with frontmatter; `name` must match the directory. Pick the plugin by role.
2. Decide invocation. Model-invoked pays context load every turn — pick it only when the agent or another skill must reach the skill unprompted. Otherwise `disable-model-invocation: true`.
3. Add the row to this README table and place it in the right chain.
4. A step that runs another plugin's skill needs that plugin in `dependencies` (plugin.json); a mention only says "(<plugin>, if installed)". `bash scripts/check.sh` enforces both.
5. Only add to the `for entry in …` loop in `plugins/thang-core/scripts/init.sh` if a project needs its own copy.
