# thang-progress

Shows a skill's checklist when it starts and each checkpoint as it completes (✅ 3/6), then 🏁 when all are done. Never blocks.

## Install

```
/plugin marketplace add thanghokdps/claude-root
/plugin install thang-progress@thang-kit
```

No other plugin needed.

## Hooks

| Event | Script |
|-------|--------|
| PostToolUse (Skill) | `skill-progress.sh` |
| UserPromptExpansion | `skill-progress.sh` |
| TaskCreated | `skill-progress.sh` |
| TaskCompleted | `skill-progress.sh` |
| Stop | `skill-progress.sh` |

## What you see

- A skill starts → `📋 /agent-tool — 4 checkpoints: Detect and place · Contract first · …`
- Each checkpoint done → `✅ (2/4) Contract first`
- End of turn → `⏳ 2/4 done — open: …`, `🏁 Checklist complete — 4/4`, or `⏹ Checklist closed — ✅ 1 done · ⏭ 3 skipped` (skipped is never reported as complete)

Works for any skill with `## Step` / `## Stage` / `## Phase` headings or `**Done when:**` lines. With the task panel on (`/config` → todo / task tracking, or `CLAUDE_CODE_ENABLE_TASKS=1`) each checkpoint is a task and ✅ appears the moment it completes; without it, Claude writes `✅ <step>` / `⏭ <step>` lines and the tally appears at the end of the turn. Needs `python3`; without it the hooks stay silent. Never blocks anything.

All plugins: [`../README.md`](../README.md).
