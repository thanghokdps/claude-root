---
model: opus
effort: high
name: mobile-feature
description: Builds or changes a screen or flow in a React Native / Expo app the way the repo already builds them — typed navigation params, the data hook, every state (loading, empty, error, submitting with back blocked), platform differences (keyboard, safe area, permissions) handled per OS, theme tokens instead of raw values, accessibility props on every control. Proves it with React Native Testing Library tests and a run on the iOS Simulator and the Android emulator. Use when the user asks for a mobile screen, flow, form or sheet, or to fix screen behaviour on iOS or Android.
when_to_use: mobile screen, "làm màn hình mobile", "màn hình trên app", React Native screen, Expo screen, navigation flow, bottom sheet, form on mobile, keyboard covers input, safe area, iOS only bug, Android only crash, permission prompt camera notifications, "chạy thử trên simulator"
---

# mobile-feature

**Invoke:** `/mobile-feature <what the user should see and do, and on which platforms>`

Rules: `app-structure.md` and `testing.md` from core, plus `${CLAUDE_PLUGIN_ROOT}/rules/react-native.md`. A web page is `/ui-feature` (frontend, if installed); the store release is `/release-checklist` (ship, if installed); a chat screen on CopilotKit is `/agent-frontend` (ai, if installed).

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| Screens | `src/screens/<Flow>/`, `app/` (Expo Router), the navigator that mounts them |
| Navigation types | the `ParamList` type, the screen-name constants, `useNavigation` / `useRoute` typing |
| Primitives | `components/ui/` or the design-system package: `Button`, `TextInput`, `Sheet`, icons |
| Theme | `makeStyles` / `useTheme`, NativeWind, the tokens file |
| Data | the request helper and its retry policy, TanStack Query hooks (`useGet*`, `useCreate*`), the backend's exported types |
| Platform handling | `Platform.OS` guards, safe-area provider, keyboard-avoiding pattern, permissions library |
| Tests | `@testing-library/react-native` setup, navigation mocks in `moduleNameMapper`, existing screen tests |
| Platforms | which of iOS / Android the app ships to (`app.json`, `eas.json`, `ios/`, `android/`) |

**Done when:** each row names a path. The screen's states are listed: default, loading, empty, error, and for writes submitting, succeeded and failed, plus any platform-specific state (permission denied, offline).

## Step 2 — Tests first, from what the user sees

Write React Native Testing Library tests for the states and interactions in Step 1, with the data hook mocked at the request boundary and navigation mocked the way the repo already mocks it:

- Query by role and accessible name (`getByRole("button", { name: "Save" })`), falling back to `testID` only when no role fits.
- One test per state from Step 1, one per interaction (press, type, submit), one for the navigation call with its typed params.
- A platform-specific behaviour gets a test per platform (`Platform.OS` mocked).

**Done when:** the tests exist and fail for the right reason (the screen or state does not exist yet).

## Step 3 — Build

- Place it per the repo's layout: the screen in its flow folder, named export, typed as `<Stack>ScreenProps<typeof SCREENS.X>`; screen-internal pieces beside it, reusable ones in the primitives package.
- Use the primitives. No raw `<TouchableOpacity>` / `<TextInput>` outside them, no raw hex or one-off numbers (theme tokens only), icons from the one set at its sizes.
- Data: the repo's request helper with the policy the operation needs (reads retry, writes do not), hooks named `useGet*` / `useCreate*`, types imported from the backend schema, never re-declared.
- Every state is real UI: skeleton or spinner, an empty state with the next action, an error with retry, controls disabled and back navigation blocked while submitting, success feedback then navigate.
- Platform: `Platform.OS` guards where iOS and Android differ (keyboard, safe area, permissions, haptics); permission checked before the native API is used, with a denied state the user can act on.
- Accessibility: `accessibilityRole` on every control, `accessibilityLabel` when there is no visible text, `testID` on what tests target.
- Lists: `FlashList` / `FlatList` with `keyExtractor`, no anonymous render functions re-created per item; heavy work off the JS thread.

**Done when:** the Step 2 tests pass, plus typecheck and lint, and `grep -rnE "#[0-9a-fA-F]{3,8}" src --include=*.tsx` finds nothing outside the theme.

## Step 4 — Prove it on a device

Build and launch on the iOS Simulator (the iOS Simulator tool, or `npx expo run:ios` / `npx expo start` with the dev client) and, when the app ships to Android, the emulator. Drive the happy path and one failure state on each; screenshot each state; check Metro / the device log has no red box or unhandled promise.

**Done when:** screenshots per platform and a clean log are shown. A platform that could not be launched is named with the reason, never assumed.

---

Hand-offs: the endpoint behind the screen → `/api-endpoint` (backend, if installed) · a design to match → `/design-ui` (frontend, if installed; its token and primitive steps apply, its browser diff does not) · release → `/release-checklist` (ship, if installed) · done → `/verify-done` → `/review-checklist`.
