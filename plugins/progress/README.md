# progress

Shows a skill's checklist when it starts and each checkpoint as it completes (✅ 3/6), then 🏁 when all are done. Hooks only, never blocks.

**For:** everyone. Every other plugin depends on it, so it comes with any role. It is what lets a non-technical reader follow what Claude is doing step by step.

## Skills

None. This plugin is hooks only.

## Hooks

| Hook | Event | Does |
|---|---|---|
| `skill-progress` | after a Skill call; prompt expansion; task created; task completed; on stop | Reads the skill's `## Step` / `## Stage` / `## Phase` headings or `**Done when:**` lines and shows the checklist, each completed checkpoint, and a tally at the end of the turn |

What you see:

- A skill starts → `📋 /agent-tool — 4 checkpoints: Detect and place · Contract first · …`
- Each checkpoint done → `✅ (2/4) Contract first`
- End of turn → `⏳ 2/4 done — open: …`, `🏁 Checklist complete — 4/4`, or `⏹ Checklist closed — ✅ 1 done · ⏭ 3 skipped`. Skipped is never reported as complete.

With the task panel on (`/config` → task tracking, or `CLAUDE_CODE_ENABLE_TASKS=1`) each checkpoint is a task and ✅ appears the moment it completes; without it, Claude writes `✅ <step>` / `⏭ <step>` lines and the tally appears at the end of the turn. Needs `python3`; without it the hooks stay silent.

## Depends on

Nothing.

## Install

```text
/plugin install progress@harness
```

The marketplace must be added first (GitLab or the GitHub mirror): see the [root README](../../README.md#quickstart). All plugins: [`../README.md`](../README.md).
