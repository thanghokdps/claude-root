# Skills

Each skill is a Markdown prompt program invoked via `/skill-name` in Claude Code.

| Skill | Command | Purpose | Lanes |
|-------|---------|---------|-------|
| [init-project](init-project/SKILL.md) | `/init-project` | Scan src → generate .claude/ harness | all |
| [feature](feature/SKILL.md) | `/feature <desc>` | Risk intake → plan → build → review | tiny/normal/high |
| [fix-bug](fix-bug/SKILL.md) | `/fix-bug <symptom>` | Root cause → minimal fix → verify → commit | tiny/normal |
| [grill](grill/SKILL.md) | `/grill [target]` | Relentless one-question-at-a-time interview to harden a plan | normal/high |
| [blast-radius](blast-radius/SKILL.md) | `/blast-radius [range]` | Change-impact trace + risk score + rollback plan | normal/high |
| [code-review](code-review/SKILL.md) | `/code-review [low\|medium\|high]` | Review diff, find bugs + security issues | n/a |
| [checkpoint](checkpoint/SKILL.md) | `/checkpoint` | Progress vs plan + all quality gates | n/a |
| [sync-memory](sync-memory/SKILL.md) | `/sync-memory` | Pull latest + rebuild memory from your commits | n/a |

## Skill handoff map

```
/init-project
    ↓ (first run)
/brainstorming → design.md
    ↓
/grill → hostile interview → design.md hardened, assumptions surfaced
    ↓
/writing-plans → PLAN.md with wave-organized tasks
    ↓
/feature → risk intake → tiny: direct | normal: plan + build | high: research + plan + confirm + build
    ↓
/blast-radius → what does this reach? 🟢/🟡/🔴 + rollback plan
    ↓
/checkpoint → quality gates → ✅ continue or ❌ fix
    ↓
/code-review → findings → fix → /checkpoint again
    ↓ (team project, start of session)
/sync-memory → pull latest → memory updated → ready to work
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md`
2. Define: **Invoke**, **What it does**, stages, output format, hard gates
3. Add to this README table **and** the handoff map above
4. Add a section to the root `README.md` skill reference, and a how-to + quick-reference row to `docs/USAGE.md`
5. Update `scripts/init.sh` to copy the new skill directory (universal skills only)
6. If it should be globally available, add it to the `~/.claude/CLAUDE.md` Skills Inventory table
