# HARNESS.md — How this system works

## Two layers

| Layer | What it is | Lives in |
|-------|-----------|---------|
| **Skills** (engine) | Invocable `/skills` that do the work — feature, fix-bug, review, checkpoint | `skills/`, `agents/` |
| **Harness** (control) | Thin layer that decides how much process a change needs and when to involve a human | `hooks/`, `rules/`, memory system |

The engine answers *"how do I build this?"* The harness answers *"how careful should I be, and who needs to approve?"*

## The one principle everything turns on

> **Ceremony scales with risk. Human interruption scales with ambiguity.**

- **Risk** → how much proof and process (lanes: tiny / normal / high-risk)
- **Ambiguity** → whether a human is asked — only to confirm intent, not to classify risk

High-risk + unambiguous → runs autonomously through heavy proof.  
Low-risk + ambiguous → still pauses to ask.

## How a change flows

```
prompt → scope-gate.sh → /feature → risk intake → lane → build → quality gates → commit → memory
```

1. **`scope-gate.sh`** fires on every prompt — flags high-risk patterns, stale memory
2. **`/feature`** classifies the request: lane + confidence
3. **Lane routes the work:**

| Lane | Condition | Process |
|------|-----------|---------|
| tiny | 0–1 risk flags | Direct edit, hooks are safety net |
| normal | 2–3 flags | Research + plan before coding |
| high-risk | 4+ flags or hard gate | Full chain: research → plan → confirm → build → review |

4. **Confidence decides escalation:** low confidence at any lane → pause and ask
5. **Hooks corroborate the claim:** `commit-quality-gate.sh` checks the actual diff at commit time
6. **Memory auto-saves:** commits → `commits/`, sessions → `sessions/`

## Hard gates (always high-risk, cannot self-downgrade)

`auth · authorization · data-loss/migration · audit/security · external provider · public contract · weakening validation · high-blast file`

A hard gate discovered mid-task escalates regardless of original lane.

## Memory lifecycle

```
work starts
  ↓ scope-gate.sh reads MEMORY.md → warns if stale
  ↓
work happens
  ↓
git commit
  ↓ save-commit-memory.sh → .claude/memory/commits/YYYY-MM-DD.md
  ↓
session ends
  ↓ state-breadcrumb.sh → .claude/memory/sessions/YYYY-MM-DD.md
  ↓
user corrects Claude
  ↓ Claude saves feedback → .claude/memory/feedback/YYYY-MM-DD.md
  ↓
team project: next session
  ↓ /sync-memory → git pull + scan your commits + flag team overlaps
```

## What the hooks enforce (vs what convention asks)

| Enforced by hook | Convention only |
|-----------------|-----------------|
| No secrets in commits | Good commit messages |
| No force-push to main | Branch naming convention |
| Memory saved after commit | Filling in CLAUDE.md |
| Session breadcrumb on exit | Writing plan docs |
| Scope flags on high-risk prompt | Risk lane self-assessment |

**Rule:** What can be mechanized is a hook. Convention is the residue.

## Installing and updating

```bash
# Install
cp -r ~/Downloads/Claude ~/.claude-harness
chmod +x ~/.claude-harness/scripts/*.sh
chmod +x ~/.claude-harness/hooks/*.sh

# Update an existing project after harness changes
~/.claude-harness/scripts/init.sh /path/to/project
# (will warn before overwriting existing .claude/settings.json)

# Add a new stack rule
# 1. Create ~/.claude-harness/rules/stacks/<name>.md
# 2. Add detection in scripts/init.sh (has_signal block)
# 3. Re-run init.sh on any project that needs it
```
