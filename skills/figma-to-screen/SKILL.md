---
name: figma-to-screen
description: Figma MCP → React Native screen generator for flash-mobile-app. Fetches a Figma node, extracts design tokens and layout, then generates a complete screen component, styles, and navigation wiring. Handles both host-only screens and MFE remote+LazyLoad pairs. Use /figma-to-screen <figma-url-or-node-id> <ScreenName> [app].
model: sonnet
effort: high
when_to_use: implementing a new screen from a Figma design, translating designs to RN components faster, design-to-code workflow, adding a new MFE remote screen
---

# Figma → Screen — flash-mobile-app

Converts a Figma design node into a production-ready React Native screen in one command.
Understands the **host + remote MFE architecture** — generates the right output for each case.

## Usage

```
/figma-to-screen <figma-url> <ScreenName> [app=host]
```

Examples:
```
# Host-only screen (no remote module needed)
/figma-to-screen https://www.figma.com/design/B6OwTihXCouxhkZQUNqrTO/Agility-App?node-id=123-456 Profile host

# Remote screen — generates BOTH remote component + LazyLoad wrapper in host
/figma-to-screen 123:456 LeaveRequest timeOff
/figma-to-screen 789:012 BookingConfirmation roomBooking
```

---

## MFE Architecture Decision (do this FIRST)

Determine which type of screen to generate:

| App argument | Screen type | What to generate |
|-------------|-------------|-----------------|
| `host` | Host-only screen | Single screen in `apps/host/src/screens/<Name>/` |
| `timeOff` / `reallocation` / `roomBooking` / `mealReservation` / `maintenance` | Remote screen | **Two outputs**: (1) Remote component in `apps/<remote>/src/` + (2) `LazyLoad<Name>` wrapper in `apps/host/src/screens/` |

**Rule**: If `app` is a remote module → always generate a remote+LazyLoad pair, never a standalone screen in the remote app without a host wrapper.

---

## Step 1 — Parse input

Extract from the provided URL or node-id:
- `fileKey` — the segment after `/design/` in the URL
- `nodeId` — the `node-id` query param, convert `-` to `:` (e.g. `123-456` → `123:456`)
- `screenName` — PascalCase screen name (e.g. `LeaveRequest`)
- `targetApp` — which app to place the screen in (default: `host`)

---

## Step 2 — Fetch Figma data

```
mcp__figma__get_figma_data({ fileKey, nodeId })
```

From the result, extract:
- **Layout**: frame dimensions, flex direction, padding, gap, alignment
- **Colors**: fills → map to nearest `theme.colors.*` token (prefer semantic tokens over hex)
- **Typography**: font size, weight, line height → map to `textStyles.*` from `@repo/ui/themes/typography`
- **Components**: named sub-frames that map to existing `@repo/ui/components/*`
- **Images/Icons**: nodes with imageRef fills → note their nodeIds for download
- **Text content**: actual copy to use as placeholder strings

---

## Step 3 — Download images (if any)

For each node with an imageRef or SVG icon identified in Step 2:

```
mcp__figma__download_figma_images({
  fileKey,
  localPath: "apps/<targetApp>/src/assets/images",
  nodes: [{ nodeId, fileName: "<descriptive-name>.png" }]
})
```

---

## Step 4 — Map design to project tokens

Before generating code, resolve design values:

| Design value | Project token |
|-------------|---------------|
| Background color | `theme.colors.background.primary` / `.secondary` |
| Primary button color | `theme.colors.badge.button` |
| Text primary | `theme.colors.text.primary` |
| Text secondary | `theme.colors.text.secondary` |
| Border | `theme.metrics.borderWidth.default` |
| Spacing 4px | `theme.metrics.spacing[1]` |
| Spacing 8px | `theme.metrics.spacing[2]` |
| Spacing 16px | `theme.metrics.spacing[4]` |
| Spacing 24px | `theme.metrics.spacing[6]` |
| Border radius | `theme.metrics.spacing[2]` or `theme.metrics.spacing[3]` |

If a color has no matching token, use the closest semantic token and add a comment.

---

## Step 5 — Generate the screen file(s)

### Case A: Host-only screen

Output: `apps/host/src/screens/<ScreenName>/index.tsx`

```tsx
import React from 'react';
import { ScrollView, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { makeStyles } from '@repo/ui/themes/makeStyles';
import { useTheme } from '@repo/ui/themes/ThemeContext';

import { SCREENS } from '@repo/constants/screens';

import type { AppStackScreenProps } from '@/types/navigation';

type <ScreenName>Props = AppStackScreenProps<typeof SCREENS.<SCREEN_CONSTANT>>;

export const <ScreenName>Screen = ({ navigation, route }: <ScreenName>Props) => {
  const styles = useStyles();
  const insets = useSafeAreaInsets();

  // TODO: replace with real data hook
  // const { data, isLoading, isError } = useGet<ScreenName>Data();
  // if (isError) return <ErrorState />;
  // if (isLoading) return <LoadingSlider />;

  return (
    <ScrollView
      contentContainerStyle={[styles.content, { paddingBottom: insets.bottom }]}
      style={styles.container}
    >
      {/* Generated from Figma node: <nodeId> */}
    </ScrollView>
  );
};

const useStyles = makeStyles(theme => ({
  container: { flex: 1, backgroundColor: theme.colors.background.primary },
  content: { /* <generated from Figma> */ },
}));
```

---

### Case B: Remote screen (MFE pair)

Generate **two files**:

#### File 1 — Remote component (pure UI, prop-driven)
Output: `apps/<remote>/src/screens/<ScreenName>/index.tsx`

The remote component receives ALL data and callbacks as props from the host LazyLoad wrapper.
It has NO access to host navigation, host contexts, or host hooks.

```tsx
import React from 'react';
import { ScrollView, View } from 'react-native';

import { makeStyles } from '@repo/ui/themes/makeStyles';

// Infer these from Figma — what data/actions does the screen need?
export interface <ScreenName>Props {
  // data props (from host queries)
  items?: Array<{ id: string; label: string }>;
  isSubmitting?: boolean;

  // callback props (host handles navigation + mutations)
  onSubmit: (formData: <ScreenName>FormType) => void;
  onBack: () => void;
  onScreenBlur?: (closeModals: () => void) => void; // for cleanup on focus loss
}

export const <ScreenName> = ({
  items = [],
  isSubmitting,
  onSubmit,
  onBack,
}: <ScreenName>Props) => {
  const styles = useStyles();

  return (
    <ScrollView style={styles.container}>
      {/* Generated from Figma node: <nodeId> */}
      {/* Pure presentational — no useQuery, no useNavigation */}
    </ScrollView>
  );
};

const useStyles = makeStyles(theme => ({
  container: { flex: 1, backgroundColor: theme.colors.background.primary },
  /* <generated from Figma> */
}));
```

#### File 2 — LazyLoad wrapper in host
Output: `apps/host/src/screens/LazyLoad<ScreenName>/index.tsx`

The host wrapper owns: data fetching, mutations, navigation, error toasts.

```tsx
import React, { useCallback, useRef } from 'react';
import ErrorBoundary from 'react-native-error-boundary';
import Toast from 'react-native-toast-message';
import { StyleSheet, View } from 'react-native';

import { useFocusEffect } from '@react-navigation/native';

import { SCREENS } from '@repo/constants/screens';
import { getErrorMessage } from '@repo/utils/error';
import { useBlockBackNavigation } from '@repo/utils/useBlockBackNavigation';

import { FallbackError } from '@/components/FallbackError';
import { LoadingSlider } from '@/components/LoadingSlider';

// TODO: replace with real hook
// import { useCreate<ScreenName>, useGet<ScreenName>Data } from '@/hooks/use<ScreenName>';

import type { AppStackScreenProps } from '@/types/navigation';
import type { <ScreenName>Props } from '<remote>/<ScreenName>';

import { sentryService } from '@/services/sentryService';

type LazyLoad<ScreenName>Props = AppStackScreenProps<typeof SCREENS.<SCREEN_CONSTANT>>;

const <ScreenName>Remote = React.lazy(
  // @ts-ignore
  () => import('<remote>/<ScreenName>'),
);

export const LazyLoad<ScreenName>Screen = ({ navigation }: LazyLoad<ScreenName>Props) => {
  const closeModalsRef = useRef<(() => void) | null>(null);

  useFocusEffect(
    useCallback(() => {
      return () => {
        closeModalsRef.current?.();
      };
    }, []),
  );

  // TODO: replace stubs with real queries
  // const { data, isLoading, isError } = useGet<ScreenName>Data();
  const isLoading = false;
  const isError = false;

  const { mutate, isPending: isSubmitting } = useCreate<ScreenName>(
    () => {
      Toast.show({ type: 'success', text1: '<ScreenName> created successfully' });
      navigation.navigate(SCREENS.HOME);
    },
    (error: unknown) => {
      const apiMessage = getErrorMessage(error);
      Toast.show({
        type: 'error',
        text1: 'Failed to create <ScreenName>',
        ...(apiMessage && { text2: apiMessage }),
      });
    },
  );

  useBlockBackNavigation(isSubmitting, { navigation });

  const handleSubmit: <ScreenName>Props['onSubmit'] = (formData) => {
    mutate(formData);
  };

  const handleBack = () => {
    if (isSubmitting) return;
    navigation.goBack();
  };

  const handleScreenBlur = (closeModals: () => void) => {
    closeModalsRef.current = closeModals;
  };

  return (
    <View style={styles.container}>
      {isError && <Text>Something went wrong</Text>}
      {isLoading ? (
        <LoadingSlider />
      ) : (
        <ErrorBoundary
          FallbackComponent={FallbackError}
          onError={error => sentryService.captureException(error)}
        >
          <React.Suspense fallback={<LoadingSlider />}>
            <ScreenName>Remote
              isSubmitting={isSubmitting}
              onSubmit={handleSubmit}
              onBack={handleBack}
              onScreenBlur={handleScreenBlur}
            />
          </React.Suspense>
        </ErrorBoundary>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
});
```

---

### Generation rules (applies to both cases)

1. Each named Figma frame → becomes a `View` with a matching style
2. Text nodes → `<Text style={styles.xxx}>{placeholder}</Text>`
3. Image fills → `<Image source={require('../../../assets/images/xxx.png')} />`
4. Buttons → use `<TouchableOpacity testID="xxx-button">` with `accessibilityRole="button"`
5. Icons → map to `@repo/ui/icons/` if name matches, else use downloaded image
6. Nested flex → translate `direction: ROW` → `flexDirection: 'row'`, auto-detect wrap
7. Never use `StyleSheet.create` for theme-dependent values in remote — always `makeStyles`
8. Never hardcode colors — always `theme.colors.*`
9. **Remote components MUST NOT** use `useNavigation`, `useQuery`, or any host context

---

## Step 6 — Register navigation (new screens only)

### Add screen constant

File: `packages/constants/src/screens.ts`
```ts
<SCREEN_CONSTANT>: '<ScreenName>',
```

### Add to navigation types

File: `apps/host/src/types/navigation.ts`
```ts
[SCREENS.<SCREEN_CONSTANT>]: { /* params */ } | undefined;
```

### Register in host navigator

File: `apps/host/src/navigation/Navigation.tsx`

**Host-only screen**:
```tsx
import { <ScreenName>Screen } from '@/screens/<ScreenName>';
// ...
<Stack.Screen name={SCREENS.<SCREEN_CONSTANT>} component={<ScreenName>Screen} />
```

**Remote (MFE) screen** — always register the LazyLoad wrapper, never the remote directly:
```tsx
import { LazyLoad<ScreenName>Screen } from '@/screens/LazyLoad<ScreenName>';
// ...
<Stack.Screen name={SCREENS.<SCREEN_CONSTANT>} component={LazyLoad<ScreenName>Screen} />
```

### Export remote component (MFE only)

The remote app must export the component so Module Federation can serve it.
Check `apps/<remote>/src/index.ts` (or the federation entry) — add the export:

```ts
export { <ScreenName> } from './screens/<ScreenName>';
```

Also verify `apps/<remote>/rspack.config.js` exposes the correct entry:
```js
exposes: {
  './<ScreenName>': './src/screens/<ScreenName>/index.tsx',
}
```

---

## Step 7 — Generate stub tests

### Case A: Host-only screen
Create `apps/host/src/screens/<ScreenName>/index.test.tsx`:

```tsx
import React from 'react';
import { render } from '@repo/jest-config/test-utils';

import { <ScreenName>Screen } from '.';

const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: mockGoBack }),
  useRoute: () => ({ params: {} }),
  useFocusEffect: jest.fn(),
}));

describe('<ScreenName>Screen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders without crashing', () => {
    const { toJSON } = render(
      <<ScreenName>Screen navigation={{ navigate: mockNavigate, goBack: mockGoBack } as any} route={{ params: {} } as any} />
    );
    expect(toJSON()).not.toBeNull();
  });
});
```

### Case B: Remote component test (prop-driven, no navigation mock needed)
Create `apps/<remote>/src/screens/<ScreenName>/index.test.tsx`:

```tsx
import React from 'react';
import { fireEvent } from '@testing-library/react-native';
import { render } from '@repo/jest-config/test-utils';

import { <ScreenName> } from '.';

const defaultProps = {
  isSubmitting: false,
  onSubmit: jest.fn(),
  onBack: jest.fn(),
  onScreenBlur: jest.fn(),
};

describe('<ScreenName> (remote component)', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders without crashing', () => {
    const { toJSON } = render(<<ScreenName> {...defaultProps} />);
    expect(toJSON()).not.toBeNull();
  });

  it('calls onBack when back button is pressed', () => {
    const { getByTestId } = render(<<ScreenName> {...defaultProps} />);
    fireEvent.press(getByTestId('back-button'));
    expect(defaultProps.onBack).toHaveBeenCalledTimes(1);
  });

  it('calls onSubmit with form data when form is submitted', () => {
    // TODO: fill with real form interaction
  });
});
```

### Case B: LazyLoad wrapper test (mock the remote module)
Create `apps/host/src/screens/LazyLoad<ScreenName>/index.test.tsx`:

```tsx
import React from 'react';
import { render, waitFor } from '@repo/jest-config/test-utils';

// Mock the remote — it loads asynchronously at runtime
jest.mock('<remote>/<ScreenName>', () => ({
  <ScreenName>: ({ onSubmit, onBack }: any) => {
    const { View, TouchableOpacity, Text } = require('react-native');
    return (
      <View testID="remote-mock">
        <TouchableOpacity testID="submit-button" onPress={() => onSubmit({})}>
          <Text>Submit</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="back-button" onPress={onBack}>
          <Text>Back</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

// Mock host hooks
const mockMutate = jest.fn();
jest.mock('@/hooks/use<ScreenName>', () => ({
  useCreate<ScreenName>: jest.fn(() => ({ mutate: mockMutate, isPending: false })),
}));

const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: jest.fn() }),
  useRoute: () => ({ params: {} }),
  useFocusEffect: jest.fn(),
}));

import { LazyLoad<ScreenName>Screen } from '.';
import { SCREENS } from '@repo/constants/screens';

describe('LazyLoad<ScreenName>Screen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders remote component inside Suspense', async () => {
    const { getByTestId } = render(
      <LazyLoad<ScreenName>Screen navigation={{ navigate: mockNavigate } as any} route={{} as any} />
    );
    await waitFor(() => expect(getByTestId('remote-mock')).toBeTruthy());
  });

  it('calls mutate and navigates home on successful submit', async () => {
    const { getByTestId } = render(
      <LazyLoad<ScreenName>Screen navigation={{ navigate: mockNavigate } as any} route={{} as any} />
    );
    await waitFor(() => getByTestId('submit-button'));
    fireEvent.press(getByTestId('submit-button'));
    expect(mockMutate).toHaveBeenCalled();
  });
});
```

---

## Step 8 — Report

```
## Figma → Screen: <ScreenName>  [host-only | remote MFE]

**Source node**: <fileKey>#<nodeId>
**Type**: host-only | remote (MFE pair)

### Files created
Host-only:
- [ ] apps/host/src/screens/<ScreenName>/index.tsx
- [ ] apps/host/src/screens/<ScreenName>/index.test.tsx

Remote MFE:
- [ ] apps/<remote>/src/screens/<ScreenName>/index.tsx  (pure UI)
- [ ] apps/<remote>/src/screens/<ScreenName>/index.test.tsx
- [ ] apps/host/src/screens/LazyLoad<ScreenName>/index.tsx  (host wrapper)
- [ ] apps/host/src/screens/LazyLoad<ScreenName>/index.test.tsx

### Navigation wired
- [ ] packages/constants/src/screens.ts — SCREEN_CONSTANT added
- [ ] apps/host/src/types/navigation.ts — param type added
- [ ] apps/host/src/navigation/Navigation.tsx — Stack.Screen registered

### MFE wiring (remote only)
- [ ] apps/<remote>/src/index.ts — component exported
- [ ] apps/<remote>/rspack.config.js — exposes entry verified

### Design mappings
| Figma layer | RN element | Style key | Theme token |
|------------|-----------|-----------|------------|
| <...>      | <...>     | <...>     | <...>      |

### Manual TODOs
- Replace stub data hooks with real queries
- Fill in navigation params type
- Fill in remote component prop types from actual Figma interaction
- Download remaining icon assets if not auto-fetched
```

---

## Rules

- NEVER hardcode hex colors — always map to `theme.colors.*`
- NEVER use `StyleSheet.create` for theme values
- ALWAYS add `testID` to every interactive element
- ALWAYS use `useSafeAreaInsets` for bottom/top padding
- Screen must be a named export (not default export)
- If Figma node is too large (>500 lines result), fetch with `depth: 2` first to understand top-level structure, then drill into sub-nodes
