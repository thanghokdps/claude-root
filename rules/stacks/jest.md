# Jest Testing Rules

Universal rules for Jest-based test suites. Applies to both JavaScript and TypeScript projects.

---

## Test structure

### Arrange → Act → Assert (always in this order)

```ts
it('returns null when user is not found', async () => {
  // Arrange
  const repo = new UserRepository(mockDb)

  // Act
  const result = await repo.findById('non-existent-id')

  // Assert
  expect(result).toBeNull()
})
```

Never mix concerns across these three phases. If setup is complex, extract to `beforeEach`.

### `describe` and `it` / `test` blocks

- `describe`: the **thing being tested** — a class, function, module, or component
- `it` / `test`: the **behavior** — what it does under specific conditions

```ts
describe('UserService', () => {
  describe('createUser', () => {
    it('returns the created user when input is valid', async () => { ... })
    it('throws ValidationError when email is missing', async () => { ... })
    it('throws ConflictError when email already exists', async () => { ... })
  })

  describe('deleteUser', () => {
    it('soft-deletes the user record', async () => { ... })
    it('throws NotFoundError when user does not exist', async () => { ... })
  })
})
```

### Test naming — describe the behavior, not the implementation

```ts
// Good — describes what the system does
it('sends a welcome email after successful registration')
it('returns 401 when the token is expired')
it('does not exceed the rate limit for the same IP')

// Bad — describes implementation details
it('calls sendEmail')
it('throws an error')
it('test auth middleware')
```

---

## File conventions

- Test file mirrors source file: `user-service.ts` → `user-service.test.ts`
- Co-locate tests next to source: `src/users/user-service.test.ts`
- Integration test files: `*.integration.test.ts` or `__tests__/integration/`
- E2E test files: `*.e2e.test.ts` or `e2e/` directory
- Shared test utilities: `src/__tests__/helpers/` or `src/test-utils/`

---

## Assertions

### One logical concept per test

Multiple `expect` calls are fine **if they test the same concept**:

```ts
// Good: all three assertions confirm the same behavior
it('creates a user with correct default values', async () => {
  const user = await createUser({ name: 'Alice', email: 'alice@example.com' })
  expect(user.role).toBe('viewer')
  expect(user.isActive).toBe(true)
  expect(user.createdAt).toBeDefined()
})

// Bad: tests two unrelated behaviors in one test
it('creates a user and sends an email', async () => {
  const user = await createUser(...)       // behavior 1
  expect(mailer.send).toHaveBeenCalled()  // behavior 2 — separate test
})
```

### Prefer specific matchers

```ts
// Good — clear failure messages
expect(result).toEqual({ id: 1, name: 'Alice' })
expect(items).toHaveLength(3)
expect(fn).toThrow(ValidationError)
expect(str).toMatch(/^[a-z]+$/)
expect(num).toBeGreaterThan(0)
expect(obj).toMatchObject({ status: 'active' })  // partial match

// Bad — vague, hard to debug
expect(result).toBeTruthy()
expect(items.length).toBe(3)
expect(!!err).toBe(true)
```

### Testing thrown errors

```ts
// Sync
expect(() => parseJson('bad json')).toThrow(SyntaxError)
expect(() => validateAge(-1)).toThrow('Age must be positive')

// Async
await expect(fetchUser('bad-id')).rejects.toThrow(NotFoundError)
await expect(createUser({})).rejects.toMatchObject({ code: 'VALIDATION_FAILED' })
```

---

## Mocking

### Principle: mock at the boundary, not internally

- Mock **external services** (HTTP, email, S3, payment providers)
- Mock **system boundaries** (filesystem, timers, `Date`, `Math.random`)
- Do NOT mock internal modules just to isolate them — that tests implementation, not behavior

### `jest.fn()` — mock a function

```ts
const mockSendEmail = jest.fn()
mockSendEmail.mockResolvedValue({ messageId: 'abc123' })

// Assert calls
expect(mockSendEmail).toHaveBeenCalledTimes(1)
expect(mockSendEmail).toHaveBeenCalledWith(
  expect.objectContaining({ to: 'alice@example.com' })
)
```

### `jest.spyOn()` — spy on a real method

```ts
// Spy without changing behavior
const spy = jest.spyOn(console, 'error').mockImplementation(() => {})

// Spy and replace for this test only
jest.spyOn(userRepo, 'findById').mockResolvedValue(null)

// Always restore after the test
afterEach(() => jest.restoreAllMocks())
```

### `jest.mock()` — mock an entire module

```ts
// Mock the module — runs before imports (jest hoists this)
jest.mock('@/lib/mailer', () => ({
  sendEmail: jest.fn().mockResolvedValue({ messageId: 'test-id' }),
}))

// Import AFTER jest.mock (or TypeScript will complain)
import { sendEmail } from '@/lib/mailer'
import { UserService } from './user-service'

// Access the mock in tests
const mockSendEmail = sendEmail as jest.MockedFunction<typeof sendEmail>
```

**TypeScript: use `jest.Mocked<T>` for typed mocks**

```ts
import type { UserRepository } from './user-repository'

const mockRepo = {
  findById: jest.fn(),
  create: jest.fn(),
  delete: jest.fn(),
} satisfies jest.Mocked<UserRepository>
```

### Reset mocks between tests

```ts
// In jest.config.ts — preferred: automatic reset
export default {
  clearMocks: true,       // clears mock.calls and mock.instances
  resetMocks: true,       // resets implementations too
  restoreMocks: true,     // restores spied methods
}

// OR per-test in beforeEach
beforeEach(() => {
  jest.clearAllMocks()
})
```

**Rule:** Never rely on mock state from a previous test. Tests must be independent.

### Partial mocks with `jest.requireActual`

```ts
jest.mock('@/lib/config', () => ({
  ...jest.requireActual('@/lib/config'),   // keep real implementation
  featureFlags: { newDashboard: true },    // override only what you need
}))
```

---

## Async testing

### Always `await` async assertions

```ts
// Good
it('fetches the user', async () => {
  const user = await getUser('123')
  expect(user.name).toBe('Alice')
})

// Bad — test passes even if the Promise rejects
it('fetches the user', () => {
  getUser('123').then(user => {
    expect(user.name).toBe('Alice')    // this assertion may never run
  })
})
```

### Fake timers for `setTimeout`, `setInterval`, `Date`

```ts
beforeEach(() => {
  jest.useFakeTimers()
  jest.setSystemTime(new Date('2026-01-01'))
})

afterEach(() => {
  jest.useRealTimers()
})

it('expires the session after 30 minutes', () => {
  const session = createSession()
  jest.advanceTimersByTime(30 * 60 * 1000)
  expect(session.isExpired()).toBe(true)
})
```

**Rule:** Never `await new Promise(r => setTimeout(r, N))` in tests — always use fake timers.

### Testing Promises that should resolve/reject

```ts
// Resolve — use async/await
it('resolves with user data', async () => {
  const result = await fetchUser('123')
  expect(result).toEqual({ id: '123', name: 'Alice' })
})

// Reject — use rejects.toThrow
it('rejects with NotFoundError', async () => {
  await expect(fetchUser('missing')).rejects.toThrow(NotFoundError)
})

// Multiple assertions on rejection
it('rejects with correct error details', async () => {
  const error = await fetchUser('missing').catch(e => e)
  expect(error).toBeInstanceOf(NotFoundError)
  expect(error.message).toContain('missing')
})
```

---

## Setup and teardown

```ts
describe('UserRepository', () => {
  let db: Database
  let repo: UserRepository

  beforeAll(async () => {
    db = await createTestDatabase()   // expensive setup — once per describe block
  })

  afterAll(async () => {
    await db.close()                  // always clean up — even on failure
  })

  beforeEach(async () => {
    await db.clear()                  // reset state before each test
    repo = new UserRepository(db)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  it('creates a user', async () => { ... })
})
```

**Rules:**
- `beforeAll` / `afterAll`: expensive resources (DB connections, servers)
- `beforeEach` / `afterEach`: reset state, clear mocks
- Always clean up in `afterAll` even when tests fail — use try/finally if needed
- Do NOT share mutable state between `it` blocks — each test sets its own

---

## Test data

### Factory functions over raw literals

```ts
// Good: factory with sensible defaults — override only what matters for the test
function buildUser(overrides: Partial<User> = {}): User {
  return {
    id: crypto.randomUUID(),
    name: 'Alice Test',
    email: 'alice@test.com',
    role: 'viewer',
    isActive: true,
    createdAt: new Date('2026-01-01'),
    ...overrides,
  }
}

// Test only the relevant fields
it('blocks inactive users', () => {
  const user = buildUser({ isActive: false })
  expect(canLogin(user)).toBe(false)
})
```

### Use `crypto.randomUUID()` for IDs in tests

Never hardcode IDs like `'user-1'` across multiple tests — conflicts when tests run in parallel.

---

## Snapshot testing

- **Do NOT use snapshots for business logic** — they test nothing, just detect change
- Snapshots are acceptable for: rendered HTML of a stable UI component, serialized config files
- Always review snapshot diffs before committing — never `--updateSnapshot` blindly
- Keep snapshots small — snapshot only the part of the output that matters

```ts
// Acceptable — stable UI component with no logic
it('renders the button correctly', () => {
  const { container } = render(<PrimaryButton label="Submit" />)
  expect(container.firstChild).toMatchSnapshot()
})

// Unacceptable — snapshot of business logic output
it('calculates discount', () => {
  expect(calculateDiscount(order)).toMatchSnapshot()  // just write the number
})
```

---

## Coverage

- Target high coverage on **business logic** — not 100% everywhere
- Untested code paths are technical debt — note them in `SUMMARY.md` if skipped
- Don't write tests to hit coverage numbers — write tests to prevent regressions

```ts
// jest.config.ts — enforce coverage thresholds only on the important paths
coverageThreshold: {
  './src/domain/**': {
    lines: 90,
    functions: 90,
    branches: 80,
  }
}
```

---

## Test isolation checklist

Before every test run, confirm:
- [ ] No shared mutable state between tests
- [ ] All mocks cleared/reset in `beforeEach` or via `clearMocks: true` in config
- [ ] No file system or network I/O without mocking or in-memory substitution
- [ ] No `test.only` or `describe.only` committed to git
- [ ] No `console.log` or debug output in test files
- [ ] No hardcoded dates — use `jest.setSystemTime()` or pass date as parameter

---

## What NOT to do

- `test.only` / `describe.only` committed to git — breaks CI for everyone else
- `setTimeout` / real timers in tests — use `jest.useFakeTimers()`
- `console.log` in test files — clutters CI output
- Snapshots for business logic — just write the expected value
- Tests that depend on execution order — each test must be independently runnable
- Over-mocking internal modules — tests implementation not behavior
- Asserting on mock call counts when behavior is what matters
- `expect.assertions(N)` instead of proper async handling
- Magic values without context — extract to named constants
