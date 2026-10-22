---
paths:
  - "packages/services/src/**/*.ts"
  - "apps/*/src/services/**/*.ts"
  - "packages/hooks/src/**/*.ts"
  - "apps/*/src/hooks/**/*.ts"
---

# Service & Hook Conventions

## HTTP calls — always use `runRequestEffect`

```ts
import { runRequestEffect, REQUEST_POLICY } from '@repo/services/effectRequest';

// GET / list
const data = await runRequestEffect(() => client.get('/api/items'), REQUEST_POLICY.READ);

// POST (non-idempotent create)
await runRequestEffect(() => client.post('/api/items', body), REQUEST_POLICY.WRITE);

// PUT / PATCH (idempotent update)
await runRequestEffect(() => client.put(`/api/items/${id}`, body), REQUEST_POLICY.IDEMPOTENT_WRITE);
```

Never call `fetch`/HTTP client directly without `runRequestEffect`.

## Policy selection rule

| Operation | Policy |
|-----------|--------|
| GET, list, read | `REQUEST_POLICY.READ` (2 retries) |
| POST create | `REQUEST_POLICY.WRITE` (0 retries) |
| PUT/PATCH update | `REQUEST_POLICY.IDEMPOTENT_WRITE` (1 retry) |
| DELETE | `REQUEST_POLICY.WRITE` (0 retries) |

## TanStack Query hook naming

```ts
export const useGetRooms = () => useQuery({ ... });          // reads
export const useCreateRequest = (...) => useMutation({ ... }); // writes
export const useGetRoomsPaginated = () => useInfiniteQuery({ ... }); // paginated
```

## Query keys — always use constants

```ts
queryKey: QUERY_KEYS.rooms()          // good
queryKey: ['rooms']                   // bad — duplicates across files
```

## Invalidation after mutation

```ts
onSuccess: () => {
  queryClient.invalidateQueries({ queryKey: QUERY_KEYS.requests() });
}
```

## Error handling in components

Catch errors from mutations in `onError` callbacks — never try/catch around `mutate()`:

```ts
const { mutate } = useCreateRequest(
  onSuccess,
  (error) => {
    const msg = getErrorMessage(error);  // from @repo/utils/error
    Toast.show({ type: 'error', text1: 'Failed', text2: msg });
  },
);
```
