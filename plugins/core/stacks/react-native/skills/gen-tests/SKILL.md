---
name: gen-tests
description: Auto-generates co-located Jest + React Native Testing Library unit tests for a component or screen in flash-mobile-app. Handles host screens, MFE remote components, and LazyLoad wrappers differently. Use /gen-tests <path-to-component-or-screen>.
model: opus
effort: high
when_to_use: generating unit tests for a new component or screen, adding test coverage to existing code, TDD stub before implementation, testing LazyLoad wrappers or MFE remote components
---

# Gen Tests — flash-mobile-app

Auto-generates a complete test file for any component or screen, including MFE-specific patterns.

## Usage

```
/gen-tests <path>
```

Examples:
```
# Host screen
/gen-tests apps/host/src/screens/Home/index.tsx

# Remote component (pure UI, prop-driven)
/gen-tests apps/timeOff/src/screens/TimeOff/index.tsx

# LazyLoad wrapper in host (orchestration layer)
/gen-tests apps/host/src/screens/LazyLoadMaintenance/index.tsx

# Shared UI component
/gen-tests packages/ui/src/components/StatusBadge/index.tsx
```

---

## Step 0 — Classify the component type (MFE-aware)

Before reading the file, classify what kind of component it is:

| File path pattern | Type | Key testing strategy |
|------------------|------|---------------------|
| `apps/host/src/screens/LazyLoad*/index.tsx` | **LazyLoad wrapper** | Mock the remote module; test data fetching, mutations, navigation |
| `apps/<remote>/src/screens/*/index.tsx` or `apps/<remote>/src/components/*/index.tsx` | **Remote component** | Purely prop-driven; no navigation/context mocks needed; test all callbacks |
| `apps/host/src/screens/<Name>/index.tsx` (no LazyLoad prefix) | **Host screen** | Standard: mock navigation + hooks |
| `packages/*/src/**/*.tsx` | **Shared component** | Prop-driven; test theming, variants, accessibility |
| `apps/*/src/components/**/*.tsx` | **App component** | Semi-prop-driven; may use context |

---

## Step 1 — Read the source file

Read the target file completely. Extract:

### Props analysis
- All props in the component's `interface` or `type`
- Required vs optional props
- Callback props (`onPress`, `onChange`, `onSubmit`, etc.)
- Boolean props that change rendering (`isLoading`, `isError`, `isDisabled`)

### Hooks analysis
- TanStack Query hooks → mock the hook, test loading/error/success states
- Context hooks (`useAuth`, `useTheme`) → already mocked in global setup
- Navigation hooks (`useNavigation`, `useRoute`) → mock `@react-navigation/native`
- Custom hooks from `@/hooks/*` or `@repo/hooks/*` → mock at module level

### Interactions analysis
- Every `onPress` / `onSubmit` handler → generate a `fireEvent.press` test
- Text inputs → generate `fireEvent.changeText` test
- Conditional renders (`isLoading`, `isError`, empty states) → one test per branch

### Side effects
- `useEffect` calls with navigation → test they fire correctly
- Mutations → test success callback and error callback paths

---

## Step 2 — Identify test output path

- Source: `apps/<app>/src/screens/MyScreen/index.tsx` → Test: `apps/<app>/src/screens/MyScreen/index.test.tsx`
- Source: `packages/ui/src/components/Btn/index.tsx` → Test: `packages/ui/src/components/Btn/index.test.tsx`
- Source: `apps/<app>/src/components/Card/index.tsx` → Test: `apps/<app>/src/components/Card/index.test.tsx`

If a test file already exists, read it first and ONLY add missing test cases — do not overwrite existing tests.

---

## Step 3 — Generate mock declarations

### Standard mocks (always include)

```ts
// Navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();

jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: mockGoBack }),
  useRoute: () => ({ params: {} }),
  useFocusEffect: (cb: () => void) => cb(),
}));
```

### TanStack Query hooks

For each `useQuery`/`useMutation` hook used:
```ts
const mockUseXxx = jest.fn();
jest.mock('@/hooks/useXxx', () => ({ useXxx: (...args: any[]) => mockUseXxx(...args) }));

// Default return (success state)
beforeEach(() => {
  mockUseXxx.mockReturnValue({
    data: <minimal-fixture>,
    isLoading: false,
    isError: false,
  });
});
```

### Service mocks

```ts
jest.mock('@/services/sentryService', () => ({
  sentryService: { captureException: jest.fn() },
}));
```

### Firebase / Auth mocks

```ts
jest.mock('@react-native-firebase/auth', () => ({
  getAuth: jest.fn(() => ({ currentUser: { uid: 'test-uid' } })),
}));
```

---

## Step 4 — Generate test cases

### Base structure

```ts
import React from 'react';
import { fireEvent } from '@testing-library/react-native';
import { render, waitFor } from '@repo/jest-config/test-utils';

import { <ComponentName> } from '.';

// --- mock declarations (from Step 3) ---

describe('<ComponentName>', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // reset hook mocks to success defaults
  });

  // --- test cases (from Step 4 rules) ---
});
```

### Required test cases (generate ALL that apply)

#### 1. Render — happy path
```ts
it('renders without crashing', () => {
  const { toJSON } = render(<Component {...defaultProps} />);
  expect(toJSON()).not.toBeNull();
});
```

#### 2. Loading state (if component has isLoading prop or useQuery)
```ts
it('shows loading indicator when data is loading', () => {
  mockUseXxx.mockReturnValue({ data: undefined, isLoading: true, isError: false });
  const { getByTestId } = render(<Component {...defaultProps} />);
  expect(getByTestId('loading-indicator')).toBeTruthy();
});
```

#### 3. Error state (if component has isError)
```ts
it('shows error state when request fails', () => {
  mockUseXxx.mockReturnValue({ data: undefined, isLoading: false, isError: true });
  const { getByText } = render(<Component {...defaultProps} />);
  expect(getByText(/something went wrong/i)).toBeTruthy();
});
```

#### 4. Empty state (if data can be empty array/null)
```ts
it('shows empty state when list is empty', () => {
  mockUseXxx.mockReturnValue({ data: [], isLoading: false, isError: false });
  const { getByTestId } = render(<Component {...defaultProps} />);
  expect(getByTestId('empty-state')).toBeTruthy();
});
```

#### 5. Press/interaction handlers
```ts
it('calls onPress when button is tapped', () => {
  const onPress = jest.fn();
  const { getByTestId } = render(<Component {...defaultProps} onPress={onPress} />);
  fireEvent.press(getByTestId('<testID-from-source>'));
  expect(onPress).toHaveBeenCalledTimes(1);
});
```

#### 6. Navigation (if screen navigates on action)
```ts
it('navigates to <destination> after successful submission', async () => {
  const { getByTestId } = render(<Screen {...defaultProps} />);
  fireEvent.press(getByTestId('submit-button'));
  await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(SCREENS.<DESTINATION>));
});
```

#### 7. Mutation success + error
```ts
describe('on submit', () => {
  it('shows success toast and navigates on success', async () => {
    // trigger success callback
  });

  it('shows error toast on failure', async () => {
    // trigger error callback
  });
});
```

#### 8. Conditional render (boolean props)
```ts
it('disables button when isDisabled is true', () => {
  const { getByTestId } = render(<Component {...defaultProps} isDisabled />);
  expect(getByTestId('submit-button').props.disabled).toBe(true);
});
```

---

## Step 5 — Build minimal prop fixtures

For each required prop, infer a minimal valid value from the TypeScript type:
- `string` → `'test-value'`
- `number` → `0`
- `boolean` → `false`
- `() => void` → `jest.fn()`
- Array types → `[]`
- Enum/union → first value in the union
- Navigation props → use `mockNavigation` / `mockRoute` pattern

```ts
const defaultProps = {
  // <prop>: <minimal-value>,
};
```

---

## Step 6 — Write the test file

Write the generated file to the output path from Step 2.

Then run:
```bash
pnpm --filter <affected-app-or-package> test -- --testPathPattern="<ComponentName>"
```

If tests fail due to missing mocks or imports, fix them before reporting complete.

---

## Step 7 — Report

```
## Tests generated: <ComponentName>

**Source**: <path>
**Test file**: <test-path>

### Coverage
| Test case | Type |
|-----------|------|
| renders without crashing | render |
| shows loading state | loading branch |
| <...> | <...> |

### Skipped (needs manual impl)
- <case that needs real fixture data>

### Run
pnpm --filter <app> test -- --testPathPattern="<ComponentName>"
```

---

## MFE-specific patterns

### Testing a remote component (prop-driven)

Remote components live in `apps/<remote>/src/`. They receive everything via props — no navigation, no context.

```tsx
// No navigation mock needed
// No @react-navigation/native mock needed
// Just pass all props directly

const defaultProps: <ComponentName>Props = {
  items: [{ id: '1', label: 'Item 1' }],
  isSubmitting: false,
  onSubmit: jest.fn(),
  onBack: jest.fn(),
  onScreenBlur: jest.fn(),
};

describe('<ComponentName> (remote)', () => {
  it('renders list of items', () => {
    const { getByText } = render(<<ComponentName> {...defaultProps} />);
    expect(getByText('Item 1')).toBeTruthy();
  });

  it('calls onBack when back button pressed', () => {
    const { getByTestId } = render(<<ComponentName> {...defaultProps} />);
    fireEvent.press(getByTestId('back-button'));
    expect(defaultProps.onBack).toHaveBeenCalledTimes(1);
  });

  it('calls onSubmit with correct data when form submitted', () => {
    // fill form fields then press submit
  });
});
```

### Testing a LazyLoad wrapper

LazyLoad wrappers live in `apps/host/src/screens/LazyLoad*/`. They own data fetching + mutations.
The remote module must be mocked to avoid Module Federation resolution at test time.

```tsx
// 1. Mock the remote module FIRST (before any imports that might trigger it)
jest.mock('<remote-name>/<ComponentName>', () => ({
  <ComponentName>: ({ onSubmit, onBack, isSubmitting }: any) => {
    const { TouchableOpacity, View, Text } = require('react-native');
    return (
      <View testID="remote-mock">
        <TouchableOpacity testID="submit-button" onPress={() => onSubmit({ field: 'value' })}>
          <Text>Submit</Text>
        </TouchableOpacity>
        <TouchableOpacity testID="back-button" onPress={onBack}>
          <Text>Back</Text>
        </TouchableOpacity>
      </View>
    );
  },
}));

// 2. Mock host-side hooks (TanStack Query)
const mockMutate = jest.fn();
jest.mock('@/hooks/use<Entity>', () => ({
  useCreate<Entity>: jest.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
  useGet<Entity>Data: jest.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
}));

// 3. Mock navigation
const mockNavigate = jest.fn();
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({ navigate: mockNavigate, goBack: mockGoBack }),
  useRoute: () => ({ params: {} }),
  useFocusEffect: jest.fn(),
}));

// 4. Import component AFTER all mocks
import { LazyLoad<ScreenName>Screen } from '.';
import { SCREENS } from '@repo/constants/screens';

describe('LazyLoad<ScreenName>Screen', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders the remote component via Suspense', async () => {
    const { getByTestId } = render(
      <LazyLoad<ScreenName>Screen navigation={{ navigate: mockNavigate, goBack: mockGoBack } as any} route={{} as any} />
    );
    await waitFor(() => expect(getByTestId('remote-mock')).toBeTruthy());
  });

  it('calls mutate and navigates home on successful submit', async () => {
    const successCallback = jest.fn();
    (useCreate<Entity> as jest.Mock).mockImplementation((onSuccess) => {
      successCallback.mockImplementation(onSuccess);
      return { mutate: mockMutate, isPending: false };
    });

    const { getByTestId } = render(...);
    await waitFor(() => getByTestId('submit-button'));
    fireEvent.press(getByTestId('submit-button'));

    expect(mockMutate).toHaveBeenCalled();
    // simulate success
    successCallback();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith(SCREENS.HOME));
  });

  it('shows error state when data fetch fails', async () => {
    (useGet<Entity>Data as jest.Mock).mockReturnValue({
      data: undefined, isLoading: false, isError: true,
    });
    const { getByText } = render(...);
    await waitFor(() => expect(getByText(/something went wrong/i)).toBeTruthy());
  });
});
```

---

## Rules

- NEVER overwrite existing tests — append only
- Use `jest.clearAllMocks()` in `beforeEach`, NOT `jest.resetAllMocks()`
- Import render from `@repo/jest-config/test-utils`, NOT from `@testing-library/react-native`
- Always add `testID` annotations as TODO comments where missing in the source
- Mock at module level, not inside `it()` blocks
- If component uses `makeStyles`, no special mock needed — theme is provided by test-utils wrapper
- **For LazyLoad wrappers**: always mock the remote module — never let Module Federation resolve in tests
- **For remote components**: never add navigation or host context mocks — they're not available at runtime either
