---
name: rn-component
description: React Native component patterns for flash-mobile-app — makeStyles theming, memo, imports, accessibility, type patterns
paths:
  - "apps/*/src/components/**/*.tsx"
  - "packages/ui/src/**/*.tsx"
---

# React Native Component Patterns

## Structure

```tsx
import React, { memo } from 'react';
import { StyleSheet, View } from 'react-native';

import { makeStyles } from '@repo/ui/themes/makeStyles';
import { useTheme } from '@repo/ui/themes/ThemeContext';
import { textStyles } from '@repo/ui/themes/typography';

interface MyComponentProps {
  value: string;
  onPress?: () => void;
}

const MyComponent = ({ value, onPress }: MyComponentProps) => {
  const { theme } = useTheme();
  const styles = useStyles();

  return (
    <View style={styles.container}>
      {/* ... */}
    </View>
  );
};

const useStyles = makeStyles(theme => ({
  container: {
    backgroundColor: theme.colors.background.primary,
    padding: theme.metrics.spacing[1],
  },
}));

export default memo(MyComponent);
```

## Theming — always use `makeStyles`

- **Never** use inline styles for theme-dependent values
- Access theme tokens via `makeStyles(theme => ({ ... }))`
- For one-off theme access inside JSX use `useTheme()` directly
- Theme tokens: `theme.colors.*`, `theme.metrics.spacing[n]`, `theme.metrics.borderWidth.*`, `theme.metrics.opacity[n]`

```tsx
const useStyles = makeStyles(theme => ({
  title: {
    color: theme.colors.text.primary,
    ...textStyles.title,
  },
  button: {
    backgroundColor: theme.colors.badge.button,
    borderRadius: theme.metrics.spacing[1],
    borderWidth: theme.metrics.borderWidth.default,
    opacity: theme.metrics.opacity[80],
  },
}));
```

## Import aliases

```tsx
// Shared UI, icons, themes
import { SomeIcon } from '@repo/ui/icons/SomeName';
import { makeStyles } from '@repo/ui/themes/makeStyles';
import { useTheme } from '@repo/ui/themes/ThemeContext';
import { textStyles } from '@repo/ui/themes/typography';

// Shared packages
import { someUtil } from '@repo/utils/someUtil';
import { isAndroid, isIOS } from '@repo/utils/platform';
import { SOME_CONSTANT } from '@repo/constants/someFile';

// App-local (apps/host/src)
import { useScaling } from '@/hooks/useScaling';
import { SCREEN_WIDTH } from '@/utils/dimensions';
```

## Prop type patterns

Use discriminated unions for mutually exclusive prop variants:

```tsx
type ContentType =
  | { title: string; subtitle: string; customNode?: never }
  | { title?: never; subtitle?: never; customNode: React.ReactNode };

type MyProps = ContentType & {
  onPress?: () => void;
};
```

## Accessibility — required on interactive elements

```tsx
<TouchableOpacity
  testID="my-button"
  accessibilityRole="button"
  accessibilityLabel="Descriptive label for screen readers"
  onPress={onPress}
  activeOpacity={theme.metrics.opacity[80]}
>
```

## Platform-specific

```tsx
import { isAndroid, isIOS } from '@repo/utils/platform';

const borderRadius = isIOS() ? '40%' : '50%';
```

## Export

- Shared / reusable components → `export default memo(MyComponent)`
- Screen-internal sub-components → named export or inline, no memo needed
