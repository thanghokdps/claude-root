# TypeScript Best Practices

Universal rules for all TypeScript projects.

## Type safety

- `strict: true` always — no exceptions
- Never use `any` — use `unknown` then narrow, or a specific type
- No type assertions (`as Foo`) unless narrowing is genuinely impossible — add a comment explaining why
- Prefer `interface` for object shapes that may be extended; `type` for unions, intersections, mapped types
- Explicit return types on all exported functions — inferred types break public API contracts

## Naming

- Types/Interfaces: `PascalCase`
- Enums: `PascalCase` with `PascalCase` values (not UPPER_SNAKE)
- Generics: single letter `T`, `K`, `V` for simple; descriptive `TItem`, `TResult` for complex
- Boolean variables: `is`, `has`, `can`, `should` prefix — `isLoading`, `hasError`

## Functions

- Prefer `function` declarations for top-level named functions (hoisted, easier to stack trace)
- Arrow functions for callbacks, inline, and class methods
- Default parameters over `undefined` checks
- Destructure parameters when > 2 args: `function foo({ a, b, c }: Options)`

## Imports

- Always use explicit named imports — no `import * as`
- Type-only imports: `import type { Foo }` — prevents runtime import of type-only modules
- No barrel re-exports in performance-sensitive paths (causes full module load)

## Error handling

- Never `catch(e)` and ignore — always handle or rethrow
- Type caught errors: `catch (e) { if (e instanceof Error) { ... } }`
- Custom error classes over string messages for programmatic handling

## Async

- Always `await` Promises — never fire-and-forget without `.catch()`
- `Promise.all()` for independent parallel operations, never sequential `await` in a loop
- `Promise.allSettled()` when partial failure is acceptable

## What NOT to do

- `// @ts-ignore` or `// @ts-expect-error` without an explanation comment
- `Function` type — use specific signature `(...args: unknown[]) => unknown`
- Mutating function parameters
- `var` — always `const` or `let`
- Non-null assertion `!` on values that could genuinely be null at runtime
