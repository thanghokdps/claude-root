---
paths:
  - "**/routes/**/*.tsx"
  - "**/features/**/*.{ts,tsx}"
  - "**/locales/**"
  - "**/i18n.ts"
---

# TanStack Query, Router, Virtual and i18next rules (client-only SPA)

For a React SPA with no Server Components (`react.md` says which sections that skips). Where fetchers live and how they are named is in `references/fetchers.md`. Claims cite tanstack.com and react.i18next.com (read 2026-11-10).

## Query: one cache for server data

- Every server read goes through `useQuery` / `useInfiniteQuery` with a key from one key factory per feature (`channelKeys.messages(id)`). Never spell a key inline twice. Mutations update or invalidate those same keys.
- A mutation that returns the new object writes it with `queryClient.setQueryData` instead of refetching ([updates from mutation responses](https://tanstack.com/query/latest/docs/framework/react/guides/updates-from-mutation-responses)).
- `setQueryData` is immutable: return a new object or array from the updater, and never change the cached value in place ([updates from mutation responses](https://tanstack.com/query/latest/docs/framework/react/guides/updates-from-mutation-responses): "DO NOT attempt to write directly to the cache by mutating data").
- Realtime events patch the cache in one module, the socket handler, through the same key factory with `setQueryData`. A component never applies an event itself. Each event carries a sequence or event id. The handler drops one it has already applied and, on a gap, refetches or calls the catch-up endpoint, never guesses.
- An optimistic send uses a client-generated id that the server echoes back, so the confirmed message replaces the pending one instead of appearing twice.

## Router

- A route's critical data is loaded in its `loader` through the query client (passed in router context), so the page renders without a loading flash or a fetch waterfall ([external data loading](https://tanstack.com/router/latest/docs/framework/react/guide/external-data-loading)). The component then reads the same key with `useQuery`.
- Search params that are shareable state (a filter, the open thread) are validated with the route's schema and read through the router, never parsed by hand from `location`.
- Routes behind sign-in check the session in one parent route's `beforeLoad`, not in each page.

## Virtual: long lists

- A message list or any list that can pass a few hundred rows uses `@tanstack/react-virtual`. Give it `getItemKey` (the message id, memoised) so measurements follow the item, not its index, and `measureElement` for rows of varying height ([virtualizer](https://tanstack.com/virtual/latest/docs/api/virtualizer)).
- Loading older messages at the top keeps the reader's position: restore the scroll offset after the page is prepended, and test it with a long thread.

## i18next: every UI string in a file

- Every user-visible string, aria-label and title included, comes from `t('key')` (`useTranslation`) or `<Trans>` for markup inside a sentence ([react-i18next](https://react.i18next.com/)). A literal string in JSX is a defect, as is a string built by concatenating translated pieces.
- Keys are grouped by feature (`channel.create.title`), and every locale file has the same keys; a check in CI fails on a missing one. Plurals and counts use i18next's `count` option, never `n + ' messages'`.
- Dates, times and numbers are formatted with `Intl` in the user's locale and time zone, not with string templates.

## Tests

- Components are tested with a real `QueryClient` per test (retries off) and a mocked network at the fetch boundary, never a mocked `useQuery`. A socket-handler test applies an out-of-order and a duplicate event and checks the cache.
- Tests render with the real i18n setup and the default locale, so a missing key shows up as a failed assertion on the visible text.
