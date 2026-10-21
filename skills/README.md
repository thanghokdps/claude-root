# Skills

Each skill is a Markdown prompt program invoked via `/skill-name` in Claude Code.

| Skill | Command | Purpose | Lanes |
|-------|---------|---------|-------|
| [init-project](init-project/SKILL.md) | `/init-project` | Scan src → generate .claude/ harness | all |
| [feature](feature/SKILL.md) | `/feature <desc>` | Risk intake → plan → build → review | tiny/normal/high |
| [fix-bug](fix-bug/SKILL.md) | `/fix-bug <symptom>` | Tight red loop → minimise → hypothesise → fix → regression test | tiny/normal |
| [review-checklist](review-checklist/SKILL.md) | `/review-checklist [PR]` | correctness → tests → readability → security → scope; ≥3 actionable comments | n/a |
| [ci-triage](ci-triage/SKILL.md) | `/ci-triage [run]` | Red build → regression / flaky / environment + one-sentence root cause | n/a |
| [release-checklist](release-checklist/SKILL.md) | `/release-checklist <version>` | Scope → gates → migrations → notes → tag → deploy → smoke → rollback | high |
| [write-migration](write-migration/SKILL.md) | `/write-migration <change>` | Expand/contract, reversible, batched backfill, tested down path | high |
| [verify-done](verify-done/SKILL.md) | `/verify-done` | Fresh evidence for the "done when" check before claiming completion | all |
| [finish-branch](finish-branch/SKILL.md) | `/finish-branch` | Verify → PR/MR, merge, keep or discard → clean up worktree | n/a |
| [diagnose-session](diagnose-session/SKILL.md) | `/diagnose-session [id]` | Transcript evidence for misfires, ignored plans, noisy hooks → kit fix | n/a |
| [retro](retro/SKILL.md) | `/retro [since]` | Weekly retro from commits/PRs/CI → ≤3 things to standardize | n/a |
| [checkpoint](checkpoint/SKILL.md) | `/checkpoint` | Progress vs plan + all quality gates | n/a |
| [sync-memory](sync-memory/SKILL.md) | `/sync-memory` | Pull latest + rebuild memory from your commits | n/a |
| [brainstorming](brainstorming/SKILL.md) | `/brainstorming` | Rough idea → `specs/<slug>/design.md` | normal/high |
| [grill](grill/SKILL.md) | `/grill [target]` | Adversarial one-question-at-a-time interview that hardens a design | normal/high |
| [writing-plans](writing-plans/SKILL.md) | `/writing-plans` | Approved design → wave-organized `PLAN.md` | normal/high |
| [domain-model](domain-model/SKILL.md) | `/domain-model` | Ubiquitous language → `.claude/docs/glossary.md` + ADRs | normal/high |
| [tdd](tdd/SKILL.md) | `/tdd` | Red → green loop, one seam and one slice per cycle | all |
| [codebase-design](codebase-design/SKILL.md) | `/codebase-design` | Deep-module vocabulary — depth, seam, leverage, locality | reference |
| [writing-skills](writing-skills/SKILL.md) | `/writing-skills` | How to author and prune skills in this harness | reference |
| [coordinator](coordinator/SKILL.md) | `/coordinator <req>` | Classify intent → lane → dispatch. The router | all |
| [project-init](project-init/SKILL.md) | `/project-init` | Full `.claude/` bootstrap — docs, agents, hooks, rules | all |
| [review-diff](review-diff/SKILL.md) | `/review-diff` | Diff walkthrough with Mermaid architecture diagrams | n/a |
| [create-pr](create-pr/SKILL.md) | `/create-pr` | Branch diff → PR description | n/a |
| [verify-feature](verify-feature/SKILL.md) | `/verify-feature` | Lint + typecheck + tests across affected workspaces | n/a |
| [gen-tests](gen-tests/SKILL.md) | `/gen-tests <path>` | Scaffold tests for code that already exists | n/a |
| [compact](compact/SKILL.md) | `/compact` | Summarize session → HANDOFF.md + memory | n/a |
| [compound](compound/SKILL.md) | `/compound` | Crystallize session learnings → `docs/solutions/` | n/a |
| [btw](btw/SKILL.md) | `/btw <question>` | Quick lookup mid-task, no tasks or side effects | n/a |
| [figma-to-screen](figma-to-screen/SKILL.md) | `/figma-to-screen` | Figma frame → screen implementation | normal |
| [agent-architect](agent-architect/SKILL.md) | `/agent-architect [greenfield\|audit]` | AI assistant architecture: one-question interview → ADR → scaffold, or stock-vs-custom audit | normal/high |
| [agent-tool](agent-tool/SKILL.md) | `/agent-tool <tool>` | Agent tool: trusted identity, read vs mutation, retry/audit, short description, test | normal |
| [agent-hitl](agent-hitl/SKILL.md) | `/agent-hitl <write>` | Mutation behind interrupt: target resolution, pending action, confirm/cancel/replay, client render | normal/high |
| [agent-graph](agent-graph/SKILL.md) | `/agent-graph <scope>` | Agents, router, handoff, boundary rules, prompts, middleware order | normal |
| [agent-frontend](agent-frontend/SKILL.md) | `/agent-frontend <change>` | CopilotKit v2 React: provider headers, context, tool renderers, aimock e2e | normal |
| [agent-verify-turn](agent-verify-turn/SKILL.md) | `/agent-verify-turn [local\|prod-trace]` | Real turn + AG-UI stream as evidence; classify a production trace before fixing | all |
| [agent-evals](agent-evals/SKILL.md) | `/agent-evals [unit\|suite\|compare-models]` | Fake-model unit tests, judged eval suite with baseline gate, model comparison | normal |
| [agent-security](agent-security/SKILL.md) | `/agent-security [scope]` | Agent threat model: injection, confused deputy, exfiltration, trace PII, compliance mapping | high |

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

Read [`/writing-skills`](writing-skills/SKILL.md) first — it owns the how (invocation choice, information hierarchy, pruning, failure modes). The checklist:

1. Create `skills/<name>/SKILL.md` with frontmatter; `name` must match the directory.
2. Decide invocation. Model-invoked pays context load every turn — pick it only when the agent or another skill must reach the skill unprompted. Otherwise `disable-model-invocation: true`.
3. Add the row to this README table and place it in the right chain.
4. Add the row to the Skills Inventory in `~/.claude/CLAUDE.md` — that table is the index loaded every session, so an unlisted skill is an invisible one.
5. `cp -r skills/<name> ~/.claude/skills/` to install globally. Globally installed skills already reach every project; only add to the `for skill in …` loop in `scripts/init.sh` if a project needs its own copy.
