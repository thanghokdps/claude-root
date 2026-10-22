---
name: task
description: Lightweight single-task workflow for small fixes and chores in flash-mobile-app. No full coordinator ceremony. Use for single-file changes, quick bug fixes, dependency updates.
---

# Task — flash-mobile-app

For small fixes and chores that don't warrant the full `/ticket` pipeline.

## When to use
- Single-file or single-component change
- Bug fix estimated < 30 min
- Chore: dependency update, config tweak, copy change
- NOT for: new features, architecture changes, security changes, multi-package changes

## Steps

### 1. Create task
```
TaskCreate({ title: "<what needs to be done>", status: "in_progress" })
```

### 2. Load context
Read `.claude/docs/conventions.md` before touching any file.
Identify which workspace is affected: `apps/<name>` or `packages/<name>`.

### 3. Implement
- Follow naming and layer rules from `.claude/rules/project-conventions.md`
- No `console.log`, no raw fetch

### 3b. Test coverage (required — do not skip)

For every `.tsx` file created or modified:
- **No test file exists** → run `/gen-tests <path>` to create it
- **Test file already exists** → review and update affected test cases to match the change

Skip only for: config files, type-only files (`types.ts`, `constants.ts`), navigation wiring files.

### 4. Verify
```bash
pnpm --filter <affected-app-or-package> lint
pnpm --filter <affected-app-or-package> check-types
pnpm --filter <affected-app-or-package> test
```

### 5. Commit
```bash
git add <specific files>
git commit -m "[#<issue>] <type>: <description>"
```

### 6. Complete task
```
TaskUpdate({ status: "completed" })
```
