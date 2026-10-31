---
type: llm
focus:
  source: file
  path: app/change-password.tsx
---

This is `app/change-password.tsx` after the run. The repo has `types/navigation.ts` with `RootStackParamList` and Expo Router `typedRoutes` enabled.

PASS if any navigation the new screen performs (back, or replace to a route after success) uses typed routes/params (typed `href`, `useRouter` with a known route, or `RootStackParamList` updated for the new screen).
FAIL if the file is empty or missing, or navigation uses untyped string params cast with `as any`.
