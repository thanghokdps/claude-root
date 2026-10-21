# React Native Rules — flash-mobile-app

RN-specific rules all agents must follow.

## Performance

- Never run heavy computation on the JS thread — use `runOnJS` / worklets for animations
- FlatList / FlashList: always provide `keyExtractor`, consider `getItemLayout` for fixed-height items
- Avoid anonymous functions in JSX props for frequently re-rendered components — extract or memoize
- Images: use `@shopify/flash-list` not FlatList for long scrollable lists
- Memoize expensive child components with `React.memo` only when profiling shows a problem

## Platform differences

- Always add `Platform.OS` guards when behavior differs between iOS and Android
- iOS-only code: `if (Platform.OS === 'ios') { ... }`
- Never assume iOS behavior works on Android (especially keyboard, safe area, permissions)

## Navigation

- All screen names defined in `packages/constants/src/screens.ts` as `SCREENS.XXX`
- Never hardcode screen name strings
- Use typed navigation params via `AppStackParamList` (`apps/host/src/types/navigation.ts`)

## Styling

- Use `makeStyles(theme => ...)` from `@repo/ui/themes/makeStyles` for theme-aware styles
- Use NativeWind `className` for simple utility styles — do not mix with `makeStyles` in the same component
- Avoid inline styles in JSX — they create new objects on every render

## Testing

- Use `@testing-library/react-native` — not Enzyme or raw `render`
- Mock navigation: `jest.mock('@react-navigation/native', () => ({ ... }))`
- Mock `@repo/*` packages via jest `moduleNameMapper` in jest config — not inline mocks
- Never test RN internal implementation details (refs, internal state)

## Permissions / native modules

- Camera, notifications: always check permission before use
- Use `react-native-permissions` for permission management
- Firebase config files must never be committed to git (in `.gitignore`)

## Forbidden

- `console.log` — use Sentry `sentryService.captureException` or remove
- `StyleSheet.create` with hardcoded color values — use `theme.colors.*`
- Direct file system access outside designated paths
