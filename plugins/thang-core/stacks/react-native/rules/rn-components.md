---
paths:
  - "apps/*/src/components/**/*.tsx"
  - "packages/ui/src/**/*.tsx"
---

# Component Conventions

## Styling — always `makeStyles`, never inline

```tsx
// CORRECT
const useStyles = makeStyles(theme => ({
  container: { backgroundColor: theme.colors.background.primary },
}));

// WRONG — never hardcode colors or spacing
const styles = StyleSheet.create({ container: { backgroundColor: '#fff', padding: 8 } });
```

## Theme access

- Styles → `makeStyles(theme => ...)` (call hook `useStyles()` inside component)
- One-off theme value in JSX → `const { theme } = useTheme()`
- Typography → spread `...textStyles.title` / `...textStyles.body` from `@repo/ui/themes/typography`

## Accessibility — required on all interactive elements

```tsx
<TouchableOpacity
  testID="component-action"       // required for tests
  accessibilityRole="button"      // required
  accessibilityLabel="Human label" // required if no visible text
  activeOpacity={theme.metrics.opacity[80]}
  onPress={onPress}
>
```

## Export

```tsx
export default memo(MyComponent);   // reusable components
// Named export for screen-internal sub-components
```

## Prop types

- Discriminated union for mutually exclusive variants (avoid optional props that conflict)
- Base props + union type composed with `&`

## Imports order

1. React, react-native
2. Third-party libraries
3. `@repo/ui/*`, `@repo/utils/*`, `@repo/constants/*`
4. `@/components/*`, `@/hooks/*`, `@/utils/*`, `@/constants/*`
