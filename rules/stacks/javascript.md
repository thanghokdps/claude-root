# JavaScript Best Practices

Universal rules for modern JavaScript (ES2020+). Applies to both browser and Node.js environments.

---

## Syntax & language features

### Variables

- Always use `const` — use `let` only when the binding must be reassigned; never `var`
- Declare variables as close to their use as possible — not at the top of a function
- Destructure objects and arrays when extracting 2+ values

```js
// Good
const { id, name, email } = user
const [first, ...rest] = items

// Bad
var userId = user.id
let userName = user.name
```

### Strings

- Prefer template literals over concatenation — `` `Hello, ${name}` `` not `'Hello, ' + name`
- Use template literals for multi-line strings — never `\n` concatenation
- String comparisons: always use `===`, never `==`

### Objects & arrays

- Spread instead of `Object.assign` for shallow clones: `{ ...obj, key: value }`
- Use object shorthand: `{ name, id }` not `{ name: name, id: id }`
- Computed property names: `{ [key]: value }` — no dynamic bracket assignment after creation
- Array spread over `concat`: `[...arr1, ...arr2]`
- Use `Array.from()` to convert iterables; never `Array.prototype.slice.call()`
- **Never mutate function arguments** — return new values instead

```js
// Good
function addItem(items, newItem) {
  return [...items, newItem]
}

// Bad
function addItem(items, newItem) {
  items.push(newItem)   // mutates the caller's array
}
```

### Functions

- Prefer `function` declarations for top-level named functions (hoisted, better stack traces)
- Use arrow functions for callbacks, methods in objects, and inline expressions
- Default parameters over manual `|| fallback` checks

```js
// Good
function processUser(user, options = {}) {
  const { notify = true, role = 'viewer' } = options
  ...
}

// Bad
function processUser(user, options) {
  options = options || {}
  const notify = options.notify !== undefined ? options.notify : true
}
```

- Destructure parameters when 3+ arguments: use an options object
- Short functions (≤5 lines): arrow function is fine
- Functions > 20 lines with complex logic: named function declaration

---

## Modern patterns

### Optional chaining & nullish coalescing

```js
// Optional chaining — short-circuit on null/undefined
const city = user?.address?.city
const firstTag = post?.tags?.[0]
const result = obj?.method?.()

// Nullish coalescing — only falls back on null/undefined (not 0, '', false)
const count = response.count ?? 0
const label = config.label ?? 'Default'

// Do NOT use || for defaults when 0 or '' are valid values
const port = config.port ?? 3000      // correct
const port = config.port || 3000      // wrong — 0 would be replaced
```

### Logical assignment

```js
// Short-circuit assignment (readable alternatives to ternary)
user.role ??= 'viewer'          // assign only if null/undefined
config.debug ||= false          // assign only if falsy
cache.data &&= normalize(cache.data)  // assign only if truthy
```

### Destructuring with rename and defaults

```js
const { name: fullName, age = 0 } = person
const { data: { users } = {} } = response
```

### Object methods

```js
// Prefer these modern equivalents
Object.entries(obj).forEach(([key, val]) => ...)
Object.fromEntries(entries)           // build object from entries
Object.hasOwn(obj, key)               // over obj.hasOwnProperty(key)
```

---

## Async / concurrency

### Always await Promises — never fire-and-forget

```js
// Good
await sendEmail(user)

// Bad — errors are swallowed silently
sendEmail(user)   // no await, no .catch
```

### Parallel operations — `Promise.all` / `Promise.allSettled`

```js
// Good: parallel, fail-fast
const [user, posts] = await Promise.all([getUser(id), getPosts(id)])

// Good: parallel, tolerate partial failure
const results = await Promise.allSettled([task1(), task2()])
results.forEach(r => {
  if (r.status === 'fulfilled') use(r.value)
  else logError(r.reason)
})

// Bad: sequential when independent
const user = await getUser(id)
const posts = await getPosts(id)    // waits unnecessarily for getUser
```

### Never `await` in a loop for independent items

```js
// Good: batch
const results = await Promise.all(ids.map(id => fetchItem(id)))

// Bad: sequential N requests
for (const id of ids) {
  const item = await fetchItem(id)  // each waits for the previous
}
```

### Error handling in async code

```js
// At boundaries: try/catch with typed errors
async function createUser(data) {
  try {
    return await db.users.create(data)
  } catch (err) {
    if (err instanceof DatabaseError) throw new AppError('DB_FAILURE', err)
    throw err   // re-throw unknown errors — don't silently swallow
  }
}

// Never suppress unknown errors
} catch (err) {
  console.log(err)   // swallows — the caller has no idea something went wrong
}
```

### `AbortController` for cancellable operations

```js
const controller = new AbortController()

try {
  const data = await fetch(url, { signal: controller.signal })
} catch (err) {
  if (err.name === 'AbortError') return   // cancelled — not an error
  throw err
}

// Cancel when needed
controller.abort()
```

---

## Modules

- One module = one primary export; keep files focused
- Use named exports for everything except framework entry points (routes, pages)
- Import only what you use — no `import * as`
- Group imports: external libraries first, then internal modules, then relative paths
- No circular imports — if A imports B and B imports A, extract shared code to C

```js
// Good import order (with blank line between groups)
import { z } from 'zod'
import { db } from '@/lib/db'
import { formatDate } from '../utils/date'
```

---

## Error handling

### Custom error classes

```js
class AppError extends Error {
  constructor(code, message, cause) {
    super(message, { cause })
    this.name = 'AppError'
    this.code = code
  }
}

// Usage
throw new AppError('VALIDATION_FAILED', 'Email is required')
```

### Type-check caught errors

```js
} catch (err) {
  if (err instanceof AppError) {
    // handle known error
  } else if (err instanceof Error) {
    // handle generic Error
  } else {
    // unknown — wrap it
    throw new AppError('UNKNOWN', String(err), err)
  }
}
```

### Never ignore errors

```js
// Bad patterns
try { ... } catch (_) {}           // silently ignore
.catch(() => {})                    // swallow all errors
promise.catch(console.warn)         // log but not propagate — caller doesn't know
```

---

## Naming conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Variables, functions | `camelCase` | `getUserById`, `isLoading` |
| Classes, constructors | `PascalCase` | `UserService`, `ApiError` |
| Constants (true constants) | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `API_BASE_URL` |
| Private class fields | `#fieldName` | `#cache`, `#token` |
| Boolean variables | `is`, `has`, `can`, `should` prefix | `isValid`, `hasError` |
| Event handlers | `handle` or `on` prefix | `handleClick`, `onClose` |
| Factory functions | `create` prefix | `createUser`, `createConnection` |
| Async functions | name the awaited result, not the operation | `const user = await getUser()` |

---

## Code quality

### Guard clauses — fail fast, keep nesting shallow

```js
// Good
function processOrder(order) {
  if (!order) throw new AppError('INVALID', 'Order is required')
  if (!order.items.length) throw new AppError('EMPTY', 'Order has no items')
  if (order.total <= 0) throw new AppError('INVALID', 'Order total must be positive')

  return chargeCard(order)
}

// Bad
function processOrder(order) {
  if (order) {
    if (order.items.length) {
      if (order.total > 0) {
        return chargeCard(order)
      }
    }
  }
}
```

### Immutability

- Never mutate state or function arguments — always return new values
- Use `Object.freeze()` for true constants that must not be mutated
- Prefer functional array methods (`map`, `filter`, `reduce`) over imperative loops when transforming data

### Comments

- Comments explain WHY — not what (the code shows what)
- Good: `// Firebase requires token refresh before expiry, not after — see issue #412`
- Bad: `// Get user by id`
- Delete commented-out code — use `git blame` to recover it

---

## Browser-specific

- Never use `innerHTML` with user-controlled content — use `textContent` or DOMPurify
- Prefer `addEventListener` over inline `onclick` attributes
- Use `closest()` for event delegation instead of manual DOM traversal
- `localStorage` access can throw (private browsing) — wrap in try/catch at the boundary
- Use `requestAnimationFrame` for visual updates, not `setTimeout(fn, 0)`

---

## What NOT to do

- `==` equality — always `===`
- `arguments` object — use rest params `...args`
- `var` — always `const`/`let`
- `delete obj.key` on performance-critical objects — it deoptimizes V8
- `eval()` — ever, for any reason
- Extending built-in prototypes (`Array.prototype.myMethod = ...`)
- `with` statement
- Synchronous `XMLHttpRequest`
- `document.write()`
- Swallowing errors silently in catch blocks
