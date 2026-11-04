# React Native rules — read by mobile-engineer and mobile-feature

The repo's own theme, navigation types and request helper win over the names used here. Style-prop and platform facts checked against React Native 0.88, Expo SDK 58 and Android 16 docs on 2026-11-04.

## Platform

- Guard every iOS / Android difference with `Platform.OS`; never assume iOS behaviour holds on Android (keyboard, safe area, back button, permissions, file paths).
- Safe area from `react-native-safe-area-context`, not hard-coded insets. Apps targeting Android 16 are always edge-to-edge and cannot opt out, so content needs insets where it meets the edge. Keyboard: one avoiding pattern per app, reused.
- Follow each platform's idiom: no FAB or ripple in an iOS layout, no hand-built iOS chrome on Android. A shared look is a documented decision in `DESIGN.md`.
- Permissions (camera, photos, notifications, location): check before use, request once, render a denied state the user can act on. Never commit platform config that carries secrets (Firebase plist / json).

## Navigation

- Screen names are constants, never string literals. Params are typed through the app's `ParamList`; screens are typed `<Stack>ScreenProps<typeof SCREENS.X>`.
- Screens are named exports. Cleanup that depends on focus goes in `useFocusEffect`.
- Block back navigation while a write is in flight.

## Styling and components

- Theme tokens only: no raw hex, no one-off spacing, no `StyleSheet.create` with literal colours, no inline style objects in JSX (new object per render).
- Styles through the repo's theme-aware helper (`makeStyles(theme => …)` or the NativeWind class set); never both in one component.
- Interactive elements carry `accessibilityRole`, `accessibilityLabel` when no visible text, `accessibilityState` for disabled, busy, selected or expanded, and `testID` for tests. Reusable components export `memo(...)`; props with exclusive variants are discriminated unions.
- Touch targets at least 44pt on iOS and 48dp on Android, with `hitSlop` when the visual is smaller. Touchables are `Pressable` with feedback by role; pressed states do not shift layout.
- Text scales with the system setting: never `allowFontScaling={false}` app-wide. Use padding or `minHeight`, so rows grow.
- Contrast is measured, never judged by eye: 4.5:1 for text, 3:1 for large text and meaningful icons, in each theme (`/mobile-design`).
- Style props that surprise web habits: `boxShadow` and `filter` need the New Architecture; on iOS `filter` supports only `brightness` and `opacity`; `borderCurve` is iOS only. `expo-blur`'s `BlurView` on Android renders a translucent view unless `blurMethod` is set, so a blurred surface needs a background that works alone.
- Motion passes `${CLAUDE_PLUGIN_ROOT}/references/native-motion.md`, reduced motion included.

## Data

- Every request goes through the repo's request helper with the policy the operation needs: reads retry, creates and deletes do not, idempotent updates may retry once.
- TanStack Query hooks: `useGet*` for reads, `useCreate*` / `useUpdate*` for writes, keys invalidated after a write. Loading, error and empty are rendered, not skipped.
- Types come from the backend schema or a shared package, never re-declared on the client.

## Performance

- Long lists on `FlashList` (or `FlatList` with `keyExtractor` and `getItemLayout` for fixed heights); no anonymous functions in item props.
- Heavy computation and animation off the JS thread (worklets, `runOnJS` only to cross back). `React.memo` after profiling shows a problem, not before.

## Testing and logging

- `@testing-library/react-native`; navigation and shared packages mocked once in the Jest config, not inline per test. Never test refs or internal state.
- No `console.log` in app code: the repo's error reporter or nothing.
