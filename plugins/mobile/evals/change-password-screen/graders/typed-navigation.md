---
type: llm
focus: trace
---

The repo has `types/navigation.ts` with `RootStackParamList` and Expo Router `typedRoutes` enabled.

PASS if any navigation the new screen performs (back, replace to a route after success, or a link to the screen from `app/index.tsx`) uses typed routes/params (typed `href`, `useRouter` with a known route, or `RootStackParamList` updated for the new screen), and the new route is registered in the typed param list or reachable from Home.
FAIL if navigation uses untyped string params cast with `as any`, or the screen is created but never reachable and not added to the param list.
