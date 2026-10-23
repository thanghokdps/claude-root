---
paths:
  - "**/src/**/*.{ts,tsx,js,jsx,mts}"
---

# App structure (web app with its own backend)

An existing repo's layout is a fact: follow it and never add a second one. This tree is the default for a new app, or for a repo with no clear pattern. In a monorepo the same tree lives under `apps/<app>/src`.

```
src/
  app/                    # routes only: pages, layouts, route handlers. Thin; they call server/ or features/
  features/<feature>/     # one folder per user capability (auth, settings, billing …)
    components/  hooks/  api.ts   # UI owned by this feature · its hooks · its typed fetchers
    index.ts              # the only import surface for other features
  components/ui/          # primitives shared by ≥ 2 features (button, input, dialog …)
  server/<aggregate>/     # repository.ts (all SQL) · schema.ts (zod) · service.ts (when a route composes) · pure rules
  server/<system>/        # one per external API: client.ts, errors.ts, mappers.ts (+ generated types)
  server/http.ts          # the route wrapper, requireUser, parseJson, HttpError
  db/                     # ORM schema, client, migrations, seed
  lib/                    # framework-free helpers and shared types; no React, no db
  styles/                 # tokens.css (design tokens) + globals
  dev/                    # fixtures, design-states page, mocks; never imported by app code
  test-utils/             # shared test helpers, in one place only
e2e/                      # browser specs
```

- A file's folder says who owns it. Shared code moves to `components/ui/` or `lib/` when a second feature needs it, not before. A design's primitives are the exception: they go to `components/ui/` from the start.
- `app/` holds no business logic and no SQL. `server/` never imports from `features/`, `components/` or React.
- One repository per aggregate. A repository serving several aggregates is a split waiting to happen.
- Tests follow the repo's existing layout. With no tests yet, the user picks `__tests__/` beside the code or a `tests/` tree (`testing.md`).

## Size and naming

- Split a component over ~150 lines, or a module over ~200, along its seams. Extract on the third copy of a block, not the second.
- Files are kebab-case. Components are PascalCase, one per file. Hooks are `use-*.ts` exporting `use*`. Use named exports, except where the framework requires a default.
- Import through the path alias (`@/…`), never `../../..` across folders. One feature imports another only through its `index.ts`.
- `dev/` is blocked from app code by `no-restricted-imports`. CI runs format → typecheck → lint → tests.
