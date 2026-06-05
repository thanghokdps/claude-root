# sync-memory — Pull latest + rebuild memory from your commits

**Invoke:** `/sync-memory`

**When to use:** At the start of a work session on a team project, or after returning from time away.

---

## What it does

1. Pull latest code from remote
2. Find your last known commit (from `.claude/memory/commits/last-sync.txt`)
3. Scan all YOUR commits from last known → HEAD
4. Scan all TEAM commits for context (not full analysis — just titles + files)
5. Write a memory entry summarizing what changed
6. Flag any areas you should re-check (files teammates touched that you also touched)

---

## Stage 0 — Check memory state

Read `.claude/memory/MEMORY.md` and `.claude/memory/commits/last-sync.txt`.

Report:
- Last sync date
- Last commit by you that was recorded
- Whether memory is stale (> 2 days old)

## Stage 1 — Pull latest

```bash
git fetch --all --prune
git pull
```

If pull fails (conflicts): stop, report conflict files, ask user to resolve before proceeding.

## Stage 2 — Collect your commits

```bash
# Get your commits since last known
LAST=$(cat .claude/memory/commits/last-sync.txt 2>/dev/null || echo "")
if [ -n "$LAST" ]; then
  git log ${LAST}..HEAD --author="$(git config user.name)" --format="%H|%ai|%s" --no-merges
else
  git log --since="14.days" --author="$(git config user.name)" --format="%H|%ai|%s" --no-merges
fi
```

For each commit: list files changed, note if any are high-blast files.

## Stage 3 — Collect team context

```bash
git log ${LAST}..HEAD --not --author="$(git config user.name)" --format="%H|%an|%s" --no-merges | head -30
```

**Flag overlap**: if teammate changed a file you also changed since last sync → add to "re-check" list.

## Stage 4 — Write memory

Write to `.claude/memory/commits/YYYY-MM-DD.md`:
```markdown
---
name: commits-YYYY-MM-DD
description: Commits by <user> on YYYY-MM-DD; team sync
metadata:
  type: project
---

# Commits — YYYY-MM-DD

## Your commits (N)
- `<hash>` — <message> [files: ...]

## Team commits (N)  
- `<hash>` [<author>] — <message>

## Re-check (files with overlapping changes)
- <file> — you + <teammate> both modified
```

Update `.claude/memory/MEMORY.md` index.
Save latest hash to `.claude/memory/commits/last-sync.txt`.

## Stage 5 — Report

Print to user:
- N commits by you since last sync
- N commits by team
- Any overlap files to re-check
- Whether any unresolved feedback memories are still open

---

## Memory update rules

- Only YOUR commits get full detail (files, diffs summary)
- Team commits get title + author only (context, not analysis)
- Never write to `memory/feedback/` from this skill — that's manual or from correction
- Never overwrite today's session if it already exists — append

---

## Script shortcut

Instead of running stages manually:
```bash
.claude/harness/scripts/sync-team.sh
```
