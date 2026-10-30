# React Native rules — read by mobile-engineer and mobile-feature

The repo's own theme, navigation types and request helper win over the names used here.

## Platform

- Guard every iOS / Android difference with `Platform.OS`; never assume iOS behaviour holds on Android (keyboard, safe area, back button, permissions, file paths).
- Safe area from the provider, not hard-coded insets. Keyboard: one avoiding pattern per app, reused.
- Permissions (camera, photos, notifications, location): check before use, request once, render a denied state the user can act on. Never commit platform config that carries secrets (Firebase plist / json).

## Navigation

- Screen names are constants, never string literals. Params are typed through the app's `ParamList`; screens are typed `<Stack>ScreenProps<typeof SCREENS.X>`.
- Screens are named exports. Cleanup that depends on focus goes in `useFocusEffect`.
- Block back navigation while a write is in flight.

## Styling and components

- Theme tokens only: no raw hex, no one-off spacing, no `StyleSheet.create` with literal colours, no inline style objects in JSX (new object per render).
- Styles through the repo's theme-aware helper (`makeStyles(theme => …)` or the NativeWind class set); never both in one component.
- Interactive elements carry `accessibilityRole`, `accessibilityLabel` when no visible text, and `testID` for tests. Reusable components export `memo(...)`; props with exclusive variants are discriminated unions.

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
