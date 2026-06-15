# Project Conventions — flash-mobile-app

Imperative rules for all agents. Non-negotiable.

## Package manager

- Always `pnpm` — never `npm` or `yarn`
- Run workspace commands: `pnpm --filter <name> <script>`

## Commit format (enforced by hook)

```
[#<issue>] <type>: <description>
```

Types: `feat` `fix` `refactor` `chore` `docs` `test` `style` `ci` `perf`

## Layer boundaries (enforce strictly)

- Screens (`apps/*/src/screens/`): JSX + hook calls only. No API calls. No business logic.
- Hooks (`packages/hooks/src/`): TanStack Query only. No direct fetch.
- Services (`packages/services/src/`): `HttpService` only. No raw fetch/axios.
- Contexts (`apps/*/src/contexts/`): UI state only. No server state (that's TanStack Query).
- Components (`packages/ui/src/` or `apps/*/src/components/`): pure presentational or with local state. No API calls.

## Import order (enforced by eslint-plugin-simple-import-sort)

1. React + React Native built-ins
2. Third-party libraries
3. `@repo/*` workspace packages
4. `@/` intra-app imports

## Forbidden patterns

- `console.log` anywhere — use Sentry or remove
- Raw `fetch` or `axios` — use `HttpService` from `packages/services`
- `debugger` statements
- Committing `.env`, `GoogleService-Info.plist`, `google-services.json`
- Importing across app boundaries without going through `@repo/*`
- Relative paths crossing `src/` boundary — use `@/` alias

## Required patterns

- All components: `makeStyles(theme => ...)` for theme-aware styles
- All API hooks: use `useApiQuery` or `useEffectService` pattern
- All new screens: register in `SCREENS` constants + `Navigation.tsx`
- All new remote screens: add fallback in `FallbackLoadRemote`
- Test files: co-located next to source (`ComponentName/index.test.tsx`)

## Before every commit

- [ ] `pnpm --filter <app> lint` passes
- [ ] `pnpm --filter <app> check-types` passes
- [ ] `pnpm --filter <app> test` passes
- [ ] No `console.log` in staged files
- [ ] Commit message matches `[#<issue>] <type>: <description>`
