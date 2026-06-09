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

## Sub-agent rules

- Spawn sub-agents for: independent research, parallel review, isolated build tasks
- Pass all context explicitly (sub-agents have no conversation history)
- Do NOT spawn a sub-agent just to avoid doing work yourself
- Sub-agent results are not visible to the user — summarize findings in your response

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
