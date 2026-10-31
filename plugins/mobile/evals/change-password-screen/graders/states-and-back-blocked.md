---
type: llm
focus:
  source: file
  path: app/change-password.tsx
---

This is `app/change-password.tsx` after the run. The repo is Expo Router with a `Button` primitive that already takes `loading`/`disabled`.

PASS if the new screen under `app/` has real UI for loading/submitting, error (with a retry or a visible message) and success, disables the save control while submitting, AND blocks back navigation while submitting (e.g. `gestureEnabled: false` / `headerBackVisible: false` via Stack.Screen options, `BackHandler` on Android, or `usePreventRemove` / `beforeRemove`), and handles empty/invalid input before sending.
FAIL if the file is empty or missing, if submitting is only a disabled button with no back blocking, if error or submitting states are missing.
