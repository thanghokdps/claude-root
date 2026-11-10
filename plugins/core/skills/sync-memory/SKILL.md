---
effort: low
name: sync-memory
description: Pulls the latest commits and summarises what came in from git log — yours, your teammates', and files you both changed. Writes nothing. Use at the start of a session on a team project.
when_to_use: starting a session on a shared repo, or after a teammate has pushed work you have not seen
---

# sync-memory — Pull latest + summarise the new commits

**Invoke:** `/sync-memory`

**When to use:** At the start of a work session on a team project, or after returning from time away.

Git already holds the history, so this skill keeps no state file: it reads the range the pull brought in, or the last 14 days when the pull brought nothing.

---

## Run

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/sync-team.sh" "$(pwd)"
```

The script stashes uncommitted changes, pulls, prints your commits and the team's (top 20), lists files you and a teammate both changed, then restores the stash. Pull conflicts → it stops and says so: report the conflicting files and ask the user to resolve them before going on.

## Report

- N commits by you, N by the team, in the range the script names
- Every file under **Re-check**, with the teammate's commit that touched it — read that diff before editing the file
- A teammate commit that touches a hard gate (auth, migrations, `.claude/`, public contracts): name it

Nothing is written to the repo. A lesson worth keeping goes through `/compound`; a decision through Claude Code's own memory.
