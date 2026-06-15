# Orchestration rules

## Risk lanes

| Lane | Flags | Process |
|------|-------|---------|
| tiny | 0–1 | Direct edit, no plan, hooks are safety net |
| normal | 2–3 | Research brief + plan before coding |
| high-risk | 4+ or hard gate | Full chain: research → plan → user confirm → build → review |

Hard gates (always high-risk, cannot self-downgrade):
`auth · authorization · data-loss/migration · audit/security · external provider · public contract · high-blast file`

## Skill routing

- New feature → `/feature <description>` → risk intake first
- Bug fix → `/fix-bug <symptom>` → root cause before touching code
- Review changes → `/code-review [effort]`
- Check progress → `/checkpoint`
- Team sync → `/sync-memory`

## Orchestration modes — choosing the right primitive

| Mode | What holds the plan | Scale | Resumable | When to use |
|------|---------------------|-------|-----------|-------------|
| **Subagents** (Agent tool) | Claude's context | A few per turn | No | Independent research, parallel review |
| **Skills** | Instructions Claude follows | Same as subagents | No | Structured task flows |
| **Agent teams** | Shared task list | Handful of long-running peers | Teammates keep running | Long parallel workstreams |
| **Dynamic workflows** | A JS script the runtime executes | 16 concurrent, 1000 total per run | Yes (same session) | Codebase audits, large migrations, adversarial cross-check |

**Rule:** If task scope is ≥ 10 files independently changed, codebase-wide, or the orchestration is worth saving/rerunning → use a **dynamic workflow** instead of in-context wave agents.

## Sub-agent rules

- Spawn sub-agents for: independent research, parallel review, isolated build tasks
- Pass all context explicitly (sub-agents have no conversation history)
- Do NOT spawn a sub-agent just to avoid doing work yourself
- Sub-agent results are not visible to the user — summarize findings in your response

## Dynamic workflows

A dynamic workflow is a **JavaScript script** Claude writes; the runtime executes it in the background. Intermediate results live in script variables, not Claude's context — so a workflow can run thousands of agents without filling the context window.

### When to reach for a workflow

| Use it when | Don't use it when |
|-------------|-------------------|
| 10+ files need independent parallel changes | A wave of 2–6 agents handles it |
| Codebase-wide audit or migration | Changes are localized to 1–2 modules |
| Cross-checking results adversarially | Single linear pipeline suffices |
| Orchestration is worth saving and rerunning | One-off in-session coordination |

### Trigger methods

```text
ultracode: audit every API endpoint under src/routes/ for missing auth checks
```

Or naturally: "use a workflow for this", "run a workflow to migrate all X".
Or for the whole session: `/effort ultracode`

### Monitor and control

```
/workflows           list all runs, drill into phases/agents
p                    pause / resume
x                    stop agent or whole workflow
r                    restart selected agent
s                    save script as reusable command
```

### Save for reuse

| Path | Scope |
|------|-------|
| `.claude/workflows/<name>.js` | Project — shared with team via git |
| `~/.claude/workflows/<name>.js` | Personal — available in all projects |

Saved workflows become `/<name>` slash commands in autocomplete.

### Bundled workflows

| Command | What it does |
|---------|-------------|
| `/deep-research <question>` | Fan-out web research → cross-check sources → adversarial vote → cited report |

### Limits

- Max **16 concurrent agents**, **1,000 total** per run
- No mid-run user input — split sign-off stages into separate sequential workflows
- Resumable within the same Claude Code session only
- Disable: `"disableWorkflows": true` in settings.json or `CLAUDE_CODE_DISABLE_WORKFLOWS=1`

## Context budget & headroom

When context is getting large, use headroom to compress before handing off:

| Context state | Action |
|---|---|
| Output > ~8KB | `headroom_compress` MCP tool (if installed) or `/compact` |
| Session ending with failures | `headroom learn` — mines failures into corrections |
| Starting a new task after long session | `/compact` first, then continue |

Install once: `bash scripts/setup-headroom.sh` — wraps Claude CLI transparently (60–95% fewer tokens).

---

## Stopping rules (when to pause and ask)

- Confidence drops below medium
- Hard gate discovered mid-task
- Scope needs to expand beyond plan
- A teammate's recent commit conflicts with the planned approach
- Destructive action is required (delete, migrate, reset)
- Three consecutive quality gate failures

## Do NOT

- Bypass hooks (`--no-verify`, `--force`)
- Add features beyond what was asked
- Refactor code not in scope of the task
- Create helper abstractions for things used only once
- Leave half-finished implementations (fail loudly, not silently)
