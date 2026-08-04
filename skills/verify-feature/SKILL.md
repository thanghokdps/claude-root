---
name: verify-feature
description: Automated full-stack verification for flash-mobile-app — detects affected workspaces from git diff, runs lint + typecheck + tests for each, and reports pass/fail. Use /verify-feature [app] to verify before committing or after implementing a feature.
model: opus
effort: medium
when_to_use: verifying a feature before commit, confirming a fix didn't break other workspaces, pre-PR quality gate, after implementing from a ticket
---

# Verify Feature — flash-mobile-app

Runs the full quality gate for all workspaces affected by current changes.

## Usage

```
/verify-feature              # auto-detect affected workspaces from git diff
/verify-feature host         # verify a specific app
/verify-feature host timeOff # verify multiple specific apps
```

---

## Step 1 — Detect affected workspaces

```bash
git diff --name-only HEAD
```

Map changed file paths to workspace names:

| Path prefix | Workspace name |
|-------------|---------------|
| `apps/host/` | `host` |
| `apps/timeOff/` | `timeOff` |
| `apps/reallocation/` | `reallocation` |
| `apps/roomBooking/` | `roomBooking` |
| `apps/mealReservation/` | `mealReservation` |
| `apps/maintenance/` | `maintenance` |
| `apps/server/` | `server` |
| `packages/ui/` | `@repo/ui` |
| `packages/hooks/` | `@repo/hooks` |
| `packages/services/` | `@repo/services` |
| `packages/utils/` | `@repo/utils` |
| `packages/types/` | `@repo/types` |
| `packages/constants/` | `@repo/constants` |
| `packages/core/` | `@repo/core` |
| `packages/validation/` | `@repo/validation` |
| `packages/effect-utils/` | `@repo/effect-utils` |

**MFE cascade rules** — always apply:

1. **Remote app changed → also verify `host`**: The host loads remote modules at runtime. A type change, prop change, or export change in a remote can silently break the LazyLoad wrapper in host. Always include `host` when any remote app (`timeOff`, `reallocation`, `roomBooking`, `mealReservation`, `maintenance`) changes.

2. **`host` LazyLoad changed → also verify the corresponding remote**: If `apps/host/src/screens/LazyLoad<Name>` changed, the prop contract with the remote may have changed. Check that the remote still exports the expected props.

3. **Package changes cascade**: if any `packages/*` changed, add ALL apps that import it:
```bash
grep -rl "@repo/<package-name>" apps/*/src --include="*.ts" --include="*.tsx" | sed 's|apps/\([^/]*\)/.*|\1|' | sort -u
```

4. **`packages/constants/src/screens.ts` changed → verify ALL apps**: Screen constants are shared across host and all remotes.

5. **`packages/types/*` changed → verify ALL apps**: Shared types propagate everywhere.

If workspaces are explicitly provided as arguments, skip auto-detection but STILL apply MFE cascade rules on top.

---

## Step 2 — Run checks per workspace

If 3 or more workspaces are affected, print the status table before dispatching:

```
Verifying N workspaces in parallel. Current status:

| Workspace | Status |
|-----------|--------|
| host      | 🔵 Running |
| timeOff   | 🔵 Running |
| @repo/hooks | 🔵 Running |
| reallocation | ⬜ Queued |
```

For each affected workspace, run in order:

### 2a. Lint
```bash
pnpm --filter <workspace> lint
```

### 2b. Type check
```bash
pnpm --filter <workspace> check-types
```

### 2c. Tests
```bash
pnpm --filter <workspace> test -- --passWithNoTests
```

Run 2a → 2b → 2c sequentially per workspace. Stop at first failure and record it, but continue checking other workspaces.

For multiple workspaces, run each workspace's checks in parallel (use `run_in_background: true` on agents if needed).

As each workspace finishes, narrate and reprint the table:

```
host verified ✅ · 45s

| Workspace | Status |
|-----------|--------|
| host      | ✅ Done |
| timeOff   | 🔵 Running |
| @repo/hooks | ✅ Done |
| reallocation | ⬜ Queued |

* Waiting for 1 more workspace to finish
```

---

## Step 3 — Collect results

After all workspaces complete, print the final results table:

```
## Verification Report

| Workspace | Lint | Types | Tests | Status |
|-----------|------|-------|-------|--------|
| host      | ✅   | ✅    | ✅    | PASS   |
| timeOff   | ✅   | ❌    | -     | FAIL   |
| @repo/hooks | ✅ | ✅    | ✅    | PASS   |
```

---

## Step 4 — On failure: surface the error

For any FAIL:

1. Show the exact error output (first 30 lines)
2. Identify the file and line number
3. Check if it's a surface error (unused import, wrong type annotation) vs logic error

**Surface errors** (auto-fix allowed per `rules/auto-correct-scope.md` Rule 1–3):
- Unused import → remove it
- Missing type annotation → add it
- Incorrect interface member → fix it
- Import path typo → correct it

After auto-fixing surface errors, re-run the failed check.

**Logic errors** (Rule 4 — require human confirmation):
- Unexpected type mismatch in business logic
- Test assertion failures
- Navigation type errors from new screens

Report logic errors with full context and stop.

---

## Step 5 — Final report

```
## Verification Complete

**Status**: ALL PASS ✅  |  FAILURES FOUND ❌

### Summary
- Workspaces checked: <n>
- Auto-fixed: <list of surface fixes or "none">
- Remaining failures: <list or "none">

### Next step
- If ALL PASS → safe to commit: `git add <files> && git commit -m "[#<issue>] <type>: <description>"`
- If FAILURES → fix logic errors above before committing
```

---

## MFE prop contract check

When a remote component's props change (interface renamed, prop added/removed), run an additional check:

```bash
# Check that the LazyLoad wrapper in host passes all required props
grep -n "<RemoteComponent" apps/host/src/screens/LazyLoad<Name>/index.tsx
```

Compare against the remote component's exported `Props` interface. If any required prop is missing from the LazyLoad call site → report as a contract violation (logic error, requires manual fix).

---

## Integration with ticket workflow

The `/ticket` pipeline's qa-agent step calls `/verify-feature` automatically.
You can also run it manually at any point:

```
After implementing a remote screen (e.g. in timeOff):
  /verify-feature timeOff   # cascades → also verifies host automatically

After modifying LazyLoad wrapper in host:
  /verify-feature host      # also checks remote prop contract

After modifying a shared package:
  /verify-feature           # auto-detects all affected apps

Before pushing a PR:
  /verify-feature host timeOff reallocation
```

---

## Rules

- Never skip the typecheck step — it catches most integration errors
- Always run `--passWithNoTests` on test command (new workspaces may have no tests yet)
- Surface-error auto-fixes must be logged in `specs/<slug>/SUMMARY.md` under `## Deviations`
- If no workspace is affected by the diff (e.g. only docs changed), report "No app workspaces affected — skipping"
