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

## No AI SDK useChat

```typescript
// FORBIDDEN
import { useChat } from "@ai-sdk/react";
// CORRECT — use CopilotKit / AG-UI or whatever this project uses
```
