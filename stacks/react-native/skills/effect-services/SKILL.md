---
name: effect-services
description: Effect-based service layer patterns — runRequestEffect, REQUEST_POLICY, toDomainError, createRequestEffect
paths:
  - "packages/services/src/**/*.ts"
  - "apps/*/src/services/**/*.ts"
  - "packages/effect-utils/src/**/*.ts"
---

# Effect Service Layer Patterns

## `runRequestEffect` — the primary entry point

Use `runRequestEffect` to wrap any Promise-based HTTP call with timeout, retry, and error normalization:

```ts
import { runRequestEffect, REQUEST_POLICY } from '@repo/services/effectRequest';

// READ — 15s timeout, 2 retries
const data = await runRequestEffect(
  () => httpClient.get('/api/rooms'),
  REQUEST_POLICY.READ,
);

// WRITE — 15s timeout, 0 retries (no retry on mutations)
await runRequestEffect(
  () => httpClient.post('/api/requests', body),
  REQUEST_POLICY.WRITE,
);

// IDEMPOTENT_WRITE — 15s timeout, 1 retry (safe to retry)
await runRequestEffect(
  () => httpClient.put('/api/requests/123', body),
  REQUEST_POLICY.IDEMPOTENT_WRITE,
);
```

## REQUEST_POLICY reference

```ts
REQUEST_POLICY.READ             = { timeoutMs: 15_000, retries: 2 }
REQUEST_POLICY.WRITE            = { timeoutMs: 15_000, retries: 0 }
REQUEST_POLICY.IDEMPOTENT_WRITE = { timeoutMs: 15_000, retries: 1 }
```

**Rule:** GET/list → READ. POST (create) → WRITE. PUT/PATCH (update with same result) → IDEMPOTENT_WRITE. DELETE → WRITE.

## Error types from `toDomainError`

```ts
type DomainError =
  | { _tag: 'AuthError';       message: string; code?: string }
  | { _tag: 'NotFoundError';   message: string }
  | { _tag: 'TimeoutError';    message: string; timeoutMs?: number }
  | { _tag: 'ValidationError'; message: string; errors?: Record<string, string> }
  | { _tag: 'NetworkError';    message: string; statusCode?: number }
  | { _tag: 'AppError';        message: string; cause?: unknown }
```

## Composing Effects manually

When you need to compose multiple effects or add custom retry logic:

```ts
import { Effect } from 'effect';
import { createRequestEffect, toDomainError } from '@repo/services/effectRequest';
import { createError } from '@repo/effect-utils';

const fetchWithFallback = Effect.tryPromise({
  try: () => primaryClient.get('/api/data'),
  catch: toDomainError,
}).pipe(
  Effect.catchTag('NetworkError', () =>
    Effect.tryPromise({
      try: () => fallbackClient.get('/api/data'),
      catch: toDomainError,
    })
  ),
);

const result = await Effect.runPromise(fetchWithFallback);
```

## Service file structure

```ts
// packages/services/src/someService.ts
import { runRequestEffect, REQUEST_POLICY } from './effectRequest';
import { httpClient } from './httpClients';

export const someService = {
  getList: () =>
    runRequestEffect(() => httpClient.get('/api/items'), REQUEST_POLICY.READ),

  create: (body: CreateItemBody) =>
    runRequestEffect(() => httpClient.post('/api/items', body), REQUEST_POLICY.WRITE),

  update: (id: string, body: UpdateItemBody) =>
    runRequestEffect(() => httpClient.put(`/api/items/${id}`, body), REQUEST_POLICY.IDEMPOTENT_WRITE),
};
```

## Rules

- Never call `fetch`/`axios` directly — always wrap with `runRequestEffect`
- Always specify a `REQUEST_POLICY` — never pass an empty policy
- Catch `_tag: 'AuthError'` at the app boundary (navigation to login), not in individual services
- Validation errors (`_tag: 'ValidationError'`) contain `errors: Record<string, string>` — map them to form field errors
