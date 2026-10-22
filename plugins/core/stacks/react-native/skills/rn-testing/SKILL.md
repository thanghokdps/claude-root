---
name: rn-testing
description: Jest + React Native Testing Library patterns for flash-mobile-app — mocking Firebase/services/contexts, waitFor, global callback exposure
paths:
  - "**/__tests__/**/*.{ts,tsx}"
  - "**/*.test.{ts,tsx}"
  - "**/*.spec.{ts,tsx}"
---

# Testing Patterns

## Test utilities import

Always use the project's custom test utils:

```ts
import { render, waitFor } from '@repo/jest-config/test-utils';
```

## File structure

```ts
// 1. React Native / external mocks
jest.mock('@react-native-firebase/auth', () => ({ ... }));

// 2. Project service mocks
jest.mock('@/services/someService', () => ({ ... }));

// 3. If testing real implementation: unmock BEFORE import
jest.unmock('@/contexts/AuthContext');
import { AuthProvider } from '../AuthContext';

describe('ComponentName', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('does something when condition', () => { ... });

  describe('nested scenario', () => {
    it('...', async () => { ... });
  });
});
```

## Mocking Firebase

```ts
jest.mock('@react-native-firebase/auth', () => ({
  getAuth: jest.fn(() => ({
    signOut: jest.fn().mockResolvedValue(undefined),
  })),
  reload: jest.fn().mockResolvedValue(undefined),
}));
```

## Mocking service objects

```ts
jest.mock('@/services/sentryService', () => ({
  sentryService: {
    initHostApp: jest.fn(),
    captureException: jest.fn(),
    setAuthenticatedUser: jest.fn(),
    clearAuthenticatedUser: jest.fn(),
    wrap: jest.fn(c => c),   // HOC passthrough
  },
}));
```

## Exposing internal callbacks via globals

Use this pattern to test components that expose callbacks through refs or context:

```ts
// In test file
declare global {
  var triggerAuthStateChange: { current: ((user: any) => Promise<void>) | null } | undefined;
}

// Mock the provider to expose its callback
jest.mock('@repo/core/auth/CoreAuthProvider', () => {
  const React = require('react');
  return {
    CoreAuthProvider: ({ children, onAuthStateChange }: any) => {
      React.useLayoutEffect(() => {
        if (global.triggerAuthStateChange) {
          global.triggerAuthStateChange.current = onAuthStateChange;
        }
      }, [onAuthStateChange]);
      return <>{children}</>;
    },
  };
});

// In test
let triggerRef: { current: ((user: any) => Promise<void>) | null };

beforeEach(() => {
  triggerRef = { current: null };
  global.triggerAuthStateChange = triggerRef;
});

it('handles auth state change', async () => {
  render(<AuthProvider><Text /></AuthProvider>);
  await waitFor(() => expect(triggerRef.current).not.toBeNull());
  await triggerRef.current!(mockUser);
  expect(someService.setup).toHaveBeenCalled();
});
```

## Async assertions with `waitFor`

```ts
// Wait for async state update
await waitFor(() => expect(queryByText('Loaded')).not.toBeNull());

// Wait for mock to be called
await waitFor(() => expect(mockFn).toHaveBeenCalledWith(expect.objectContaining({ id: '123' })));
```

## Testing interactive components

```ts
import { fireEvent } from '@testing-library/react-native';

it('calls onPress when button tapped', () => {
  const onPress = jest.fn();
  const { getByTestId } = render(<MyComponent onPress={onPress} />);
  fireEvent.press(getByTestId('my-button'));
  expect(onPress).toHaveBeenCalled();
});
```

## Mock reset pattern

```ts
beforeEach(() => {
  jest.clearAllMocks();         // Reset call counts & return values
  // (not resetAllMocks — that removes implementations)
});
```

## Rules

- Use `jest.unmock` before importing the real module under test
- Use `jest.clearAllMocks()` not `jest.resetAllMocks()` in `beforeEach`
- Mock services at the module level, not inside `it()`
- `testID` on interactive elements enables `getByTestId()` — always add them in components
- Test file lives next to the implementation: `ComponentName/index.test.tsx` or `__tests__/ComponentName.test.tsx`
