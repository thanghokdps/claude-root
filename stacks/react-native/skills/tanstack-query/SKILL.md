---
name: tanstack-query
description: TanStack Query v5 patterns for flash-mobile-app — custom hooks, query keys, mutations, infinite queries, multi-query screens
paths:
  - "apps/*/src/hooks/**/*.ts"
  - "apps/*/src/hooks/**/*.tsx"
  - "packages/hooks/src/**/*.ts"
---

# TanStack Query Patterns

## Custom query hook

```ts
import { useQuery } from '@tanstack/react-query';
import { QUERY_KEYS } from '@repo/constants/queryKeys'; // or local constants

export const useGetMeetingRooms = () => {
  return useQuery({
    queryKey: QUERY_KEYS.meetingRooms(),
    queryFn: () => roomService.getRooms(),
  });
};
```

## Query key conventions

Centralize keys so invalidation is consistent:

```ts
export const QUERY_KEYS = {
  meetingRooms: () => ['meetingRooms'] as const,
  holidays: (year: number) => ['holidays', year] as const,
  requests: (filters?: RequestFilters) => ['requests', filters] as const,
};
```

## Mutation hook

```ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export const useCreateRequest = (
  onSuccess?: () => void,
  onError?: (error: unknown) => void,
) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: RequestParams) => requestService.create(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.requests() });
      onSuccess?.();
    },
    onError,
  });
};
```

## Consuming in a screen — multiple queries

```tsx
const { data: rooms, isLoading: isLoadingRooms, isError: isRoomsError } = useGetMeetingRooms();
const { data: roomsBooked, isLoading: isLoadingRoomsBooked, isError: isRoomsBookedError } = useGetMeetingRoomsBooked();

// Aggregate loading/error states
const isLoading = isLoadingRooms || isLoadingRoomsBooked;
const isError = isRoomsError || isRoomsBookedError;

// Derived data with useMemo
const formattedRooms = useMemo(
  () => (rooms ?? []).map(r => ({ label: r.id, value: r.id })),
  [rooms],
);
```

## Passing httpClient to shared hooks

Some shared hooks accept an `httpClient` option:

```tsx
const { data } = useGetHolidays(new Date().getFullYear(), {
  httpClient: basicAuthHttps,
});
```

## Infinite query (pagination)

```ts
import { useInfiniteQuery } from '@tanstack/react-query';

export const useGetRequestList = () => {
  return useInfiniteQuery({
    queryKey: QUERY_KEYS.requests(),
    queryFn: ({ pageParam = 1 }) => requestService.getList({ page: pageParam }),
    getNextPageParam: (lastPage) => lastPage.nextPage ?? undefined,
    initialPageParam: 1,
  });
};
```

## Rules

- Always name the hook `use<Action><Entity>` (e.g. `useGetRooms`, `useCreateRequest`)
- Wrap query functions in a service call — never put fetch logic directly in `queryFn`
- Use `isLoading` + `isError` + `data` tri-state rendering pattern
- Never share query key arrays inline — always use `QUERY_KEYS` constants
