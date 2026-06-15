---
name: debug-runbook
description: Structured debugging runbook for flash-mobile-app (RN monorepo). Use when hitting a crash, error, or unexpected behavior. Trigger phrases: "debug", "crash", "error", "why is this", "not working", "trace this".
model: sonnet
effort: high
when_to_use: debugging a crash or error, tracing unexpected behavior, investigating a production issue
---

# Debug Runbook — flash-mobile-app

Follow in order. Don't skip steps.

---

## Step 1 — Identify the layer

| Symptom | Layer | Where to look |
|---------|-------|--------------|
| Red screen (RN error boundary) | Component / Screen | Error message + stack trace |
| White screen / blank | Navigation / Module Federation | `FallbackLoadRemote`, remote load failure |
| Network request fails | Service / Hook | `packages/hooks/`, `packages/services/` |
| Module Federation error | Remote loading | `apps/host/remote-fallback-plugin.ts` |
| Firebase / auth error | Auth | `apps/host/src/services/mainHttpClient.ts` |
| Push notification not received | Notification | `apps/host/src/services/notification/` |
| Animation jank | UI thread | Use `/rn-performance` runbook |

---

## Step 2 — Read the error

```bash
# Metro bundler logs
NO_ZC=1 pnpm start:host

# On device logs (iOS)
npx react-native log-ios

# On device logs (Android)
npx react-native log-android
```

Look for: error message, stack trace, component name, file:line.

---

## Step 3 — Isolate

1. Reproduce on both iOS and Android? If iOS-only → platform-specific issue
2. Happens in host only, or also in remotes? If remote → check Module Federation
3. Happens with real API, or also with mocked data? If real API only → network/auth issue

---

## Step 4 — Common issues & fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Unable to resolve module @repo/X` | Package not built | `pnpm build` |
| `Cannot read property 'X' of undefined` | Null data from API | Add null check / loading state |
| `console.log` crash | Unrelated code left in | Remove all console.log |
| Module Federation white screen | Remote bundle failed to load | Check `FallbackLoadRemote` + remote app running |
| `SQLITE_BUSY database is locked` | Old wrangler process | Kill old process, restart dev |
| Hook rules violation | Conditional hook call | Move hook to top level |
| Navigation `setParams` on unmounted | Race condition | Check `isFocused()` before navigating |
| Firebase token expired | Token not refreshed | Check token refresh in `mainHttpClient.ts` |

---

## Step 5 — Run checks

```bash
pnpm --filter <affected-app> lint
pnpm --filter <affected-app> check-types
pnpm --filter <affected-app> test -- --testPathPattern="<component>"
```

---

## Step 6 — After fixing

Write a regression test. If this was a non-obvious constraint, add to `.claude/docs/solutions/`.
