# Skills

Each skill is a Markdown prompt program invoked via `/skill-name` in Claude Code.

| Skill | Command | Purpose | Lanes |
|-------|---------|---------|-------|
| [init-project](init-project/SKILL.md) | `/init-project` | Scan src → generate .claude/ harness | all |
| [feature](feature/SKILL.md) | `/feature <desc>` | Risk intake → plan → build → review | tiny/normal/high |
| [fix-bug](fix-bug/SKILL.md) | `/fix-bug <symptom>` | Root cause → minimal fix → verify → commit | tiny/normal |
| [code-review](code-review/SKILL.md) | `/code-review [low\|medium\|high]` | Review diff, find bugs + security issues | n/a |
| [checkpoint](checkpoint/SKILL.md) | `/checkpoint` | Progress vs plan + all quality gates | n/a |
| [sync-memory](sync-memory/SKILL.md) | `/sync-memory` | Pull latest + rebuild memory from your commits | n/a |

## Skill handoff map

```
/init-project
    ↓ (first run)
/feature → risk intake → tiny: direct | normal: plan + build | high: research + plan + confirm + build
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
3. Add to this README table
4. Add to `CLAUDE_LEGACY.md` skill catalog
5. Update `scripts/init.sh` to copy the new skill directory
