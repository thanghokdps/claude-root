# TypeScript rules

## Strict mode

TypeScript strict is required. Run before every commit:
```bash
npx tsc --noEmit
```
Zero errors, zero warnings — no exceptions.

## Type error triage

| Code | Meaning | Fix |
|------|---------|-----|
| TS2307 | Module not found | Check import path, barrel export |
| TS2345 | Wrong type assigned | Align type definitions |
| TS2531 | Possibly null | Add null guard or `!` (only if certain) |
| TS2339 | Property doesn't exist | Add to type or fix caller |
| TS2554 | Wrong argument count | Check function signature |
| TS2322 | Incompatible types | Check return type matches annotation |

Fix in dependency order — upstream errors cascade.

## Patterns

- Use `z.infer<typeof schema>` for Zod-derived types — never duplicate
- Prefer `type` over `interface` for unions; prefer `interface` for shapes that may be extended
- Never use `any` — use `unknown` + type narrowing
- `as Type` casts allowed only at API boundaries with a comment explaining why
- Enums: prefer `const` enum or string union — never numeric enum for business values

## Import style

- Use `@/` path aliases over relative `../../../`
- Barrel files (`index.ts`) for public module API only — never re-export internal details
- Never circular imports — if detected: extract shared types to a third module

## Utility types — use them, don't reinvent them

```typescript
Partial<T>              // all fields optional
Required<T>             // all fields required
Readonly<T>             // all fields readonly
Pick<T, 'a' | 'b'>     // subset of fields
Omit<T, 'password'>     // exclude fields
Record<K, V>            // dictionary
ReturnType<typeof fn>   // infer return type of a function
Parameters<typeof fn>   // infer parameter tuple
Awaited<T>              // unwrap Promise<T> → T
NonNullable<T>          // remove null | undefined
```

## Discriminated unions — prefer over optional fields

```typescript
// Bad: too many optional fields, unclear which combination is valid
interface Response {
  data?: User
  error?: string
  loading?: boolean
}

// Good: each state is explicit and exhaustive
type Response =
  | { status: 'loading' }
  | { status: 'success'; data: User }
  | { status: 'error'; error: string }

// Exhaustive switch — TypeScript will error if a case is missing
function render(res: Response) {
  switch (res.status) {
    case 'loading': return <Spinner />
    case 'success': return <UserCard user={res.data} />
    case 'error':   return <ErrorMessage error={res.error} />
  }
}
```

## Template literal types

```typescript
type EventName = `on${Capitalize<string>}`   // onFoo, onBar
type CSSUnit = `${number}${'px' | 'rem' | 'em'}`
type RouteKey = `/${string}`
```

## `satisfies` operator — validate without widening

```typescript
// Bad: type assertion loses narrowing
const config = {
  theme: 'dark',
  port: 3000,
} as Config

// Good: validates against Config but preserves literal types
const config = {
  theme: 'dark',
  port: 3000,
} satisfies Config

config.theme   // type is 'dark', not string
```

## React + TypeScript patterns

```typescript
// Component props — use interface, extend HTML element if wrapping
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'ghost'
  isLoading?: boolean
}

// Children: use React.ReactNode (not JSX.Element — too narrow)
interface LayoutProps {
  children: React.ReactNode
}

// Event handlers — use React.MouseEvent, React.ChangeEvent etc.
function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
  setValue(e.target.value)
}

// Ref type — match the DOM element
const inputRef = useRef<HTMLInputElement>(null)

// Generic component
function List<T extends { id: string }>({ items, renderItem }: {
  items: T[]
  renderItem: (item: T) => React.ReactNode
}) {
  return <ul>{items.map(item => <li key={item.id}>{renderItem(item)}</li>)}</ul>
}
```

## No AI SDK useChat

```typescript
// FORBIDDEN
import { useChat } from "@ai-sdk/react";
// CORRECT — use CopilotKit / AG-UI or whatever this project uses
```
