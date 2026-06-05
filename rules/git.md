# Git rules

## Commit conventions

- **One logical change per commit.** If you changed 3 files for the same reason → one commit. If you changed 2 files for different reasons → two commits.
- **Message format:** `<type>: <what and why in one line>`
  - Types: `feat` `fix` `refactor` `test` `docs` `chore`
  - Good: `fix: prevent double TOOL_CALL_END emit when parallel tool calls overlap`
  - Bad: `fix bug` / `changes` / `update`
- **Stage specific files** — never `git add .` without reviewing what you're staging
- **Never skip hooks** (`--no-verify`) unless user explicitly asks

## Branch rules

- Work on feature branches, not `main`/`master`/`dev`
- Branch naming: `<type>/<short-slug>` (e.g., `feat/add-date-picker`, `fix/parallel-tool-calls`)
- `branch-guard.sh` will warn before pushing directly to protected branches

## What never goes in a commit

- `.env` files (use `.env.example`)
- API keys, passwords, or secrets of any kind (enforced by `commit-quality-gate.sh`)
- `node_modules/`, `__pycache__/`, `.venv/`, build artifacts
- Files > 5MB (use git-lfs)
- Debugger breakpoints (`pdb.set_trace()`, `breakpoint()`)

## Merge strategy

- Prefer `--no-ff` merge or squash merge for feature branches → keeps history clean
- Rebase only on local/private branches — never rebase shared branches
- If merge conflict: resolve properly, do not force-push to discard

## Co-authored commits

Always add Co-Authored-By for AI-assisted commits:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```
