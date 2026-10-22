---
name: tanstack-ref
description: TanStack Query patterns for flash-mobile-app. Use when adding query hooks, mutations, cache invalidation, or understanding query state. Trigger phrases: "useQuery", "useMutation", "invalidate", "cache", "TanStack", "react-query".
model: haiku
effort: low
when_to_use: writing query hooks, mutations, cache management, loading/error states
---

# TanStack Query Reference — flash-mobile-app

All query hooks live in `packages/hooks/src/`. Use `useApiQuery` or `useEffectService` base hooks.

---

## Query hook pattern

```typescript
// packages/hooks/src/useFooQueries.ts
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useApiClients } from './useApiClients';

const FOO_KEYS = {
  all: ['foo'] as const,
  list: (userId: string) => ['foo', 'list', userId] as const,
  detail: (id: string) => ['foo', 'detail', id] as const,
};

export function useFooList(userId: string) {
  const { mainHttp } = useApiClients();

  return useQuery({
    queryKey: FOO_KEYS.list(userId),
    queryFn: () => mainHttp.get<FooItem[]>(`/v1/foo?userId=${userId}`),
    staleTime: 5 * 60 * 1000,  // 5 min
  });
}

export function useFooDetail(id: string) {
  const { mainHttp } = useApiClients();

  return useQuery({
    queryKey: FOO_KEYS.detail(id),
    queryFn: () => mainHttp.get<FooItem>(`/v1/foo/${id}`),
    enabled: !!id,
  });
}
```

---

## Mutation pattern

```typescript
export function useCreateFoo() {
  const { mainHttp } = useApiClients();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateFooInput) =>
      mainHttp.post<FooItem>('/v1/foo', data),
    onSuccess: (newItem) => {
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: FOO_KEYS.all });
      // Or optimistically update
      queryClient.setQueryData(FOO_KEYS.detail(newItem.id), newItem);
    },
  });
}
```

---

## In a screen (usage)

```typescript
// apps/host/src/screens/Foo/index.tsx
export function FooScreen() {
  const { data, isLoading, error } = useFooList(userId);
  const createFoo = useCreateFoo();

  if (isLoading) return <LoadingSlider />;
  if (error) return <FallbackError />;

  return (
    <FlatList
      data={data}
      keyExtractor={item => item.id}
      renderItem={({ item }) => <FooCard item={item} />}
    />
  );
}
```

---

## ⚠ Gotchas

- **Never put `useQuery` logic in screens** — always extract to `packages/hooks/`
- **`enabled: !!id`** — always guard queries that need an ID
- **`staleTime`** — set it; default is 0 (refetches on every focus)
- **Invalidation** — `invalidateQueries({ queryKey: ['foo'] })` invalidates ALL foo queries (list + detail)
- **`queryClient` is a singleton** — don't create new instances; use `useQueryClient()`
- **Module Federation**: `@tanstack/react-query` is a shared singleton — don't import it differently in remotes vs host
