---
description: Work on any task (feat / fix / refactor / chore) — breaks it down, implements, verifies, and commits
argument-hint: "[#issue-number] brief task description"
---

# Task Workflow

## Step 1 — Understand

Parse the argument: extract the issue number and task description.
If no argument was given, use the AskUserQuestion tool to ask:
- Issue number (if applicable)
- Task type: `feat` | `fix` | `refactor` | `chore` | `docs` | `test`
- Brief description of what needs to be done

For **bug fixes**: also ask for reproduction steps or the error message before touching any code.

## Step 2 — Plan with TaskCreate

Use `TaskCreate` to create a task list tailored to the type:

- **feat**: Analyze design → implement → write/update tests → verify
- **fix**: Reproduce bug → locate root cause → implement fix → add regression test → verify
- **refactor**: Identify scope → implement → confirm no behavior change → verify
- **chore/docs**: Identify files → update → verify

Mark the first sub-task `in_progress` immediately.

## Step 3 — Implement

Work through each sub-task:
- Mark it `in_progress` when you start
- Mark it `completed` when done
- Move to the next

Rules:
- Edit existing files, do not create unnecessary new ones
- No comments unless the WHY is non-obvious
- Use TypeScript strictly — no `any` unless unavoidable
- For bug fixes: one bug = one commit, do not fix adjacent issues in the same commit

## Step 4 — Verify

Before committing, run the relevant checks per project's `CLAUDE.md`.

Fix any errors. Mark the verify sub-task `completed` only when all checks pass.

## Step 5 — Commit

Follow the project commit convention from `CLAUDE.md`.

Stage only the relevant files. Never use `git add -A` without reviewing what's staged.

Report what was done and the commit hash.
