---
paths:
  - "**/*.{ts,tsx,mts,css}"
---

# Agent app code structure and conventions

Read by `/agent-architect` (scaffold), `/agent-design-ui` (build) and `/agent-feature` (every slice). The agent side is laid out in `skills/agent-architect/references/layouts.md`; this rule places everything else.

## Where code goes (L1; in L2 the same tree lives under `apps/web/src`)

```
src/
  app/                      # routes only: page, layout, route handlers — thin, call into features/server
  features/<feature>/       # one folder per user capability: chat, conversations, settings, billing …
    components/             # UI owned by this feature only
    hooks/  api.ts          # client hooks and the feature's fetchers
  components/ui/            # shared primitives used by ≥ 2 features (button, dialog, drawer, scroll area)
  server/<aggregate>/       # one per aggregate: repository.ts, service.ts, schema (zod)
  db/                       # drizzle/prisma schema, client, migrations, seed
  agent/                    # per layouts.md
  lib/                      # framework-free helpers (format, ids); no React, no db
  styles/                   # tokens.css (design tokens) + the CopilotKit theme
  dev/                      # fixtures, the /__design states page, mocks — never imported by app code
e2e/                        # Playwright specs + recorded AG-UI streams
evals/                      # agent evals (agent-evals), never run by `test`
```

Unit and integration tests go where the repo's convention puts them; a new repo asks the user (`__tests__/` beside the code, or a `tests/` tree outside `src/` mirroring it) — see the testing rule § Where tests live, asked as Q-T in the architect interview.

- A file's folder says who owns it. Put code in `components/ui/` or `lib/` only when a second feature needs it — not in advance.
- `app/` files hold no business logic and no SQL. Route handlers validate input with zod and call `server/<aggregate>/service.ts`.
- One repository per aggregate (conversations, messages, settings …). A repository that serves several aggregates is a split waiting to happen.

## Size and duplication

- Split a component over ~150 lines or a module over ~200 lines along its seams (sub-components, one hook per concern).
- Extract on the third copy of a block (scroll container, empty state, card shell), not the second.
- Delete unused exports, fixtures and dead states as the feature lands.

## Styling

- Colours, radii, spacing, font sizes and shadows come from tokens (`styles/tokens.css` → Tailwind theme or CSS variables). No raw hex (`[#efefef]`) and no one-off pixel values (`w-[348px]`) in components; a value the design uses once goes into the ui-map as a one-off with its element, and then into a token.
- Gate: `grep -rnE '\[#[0-9a-fA-F]{3,8}\]' src` returns nothing outside `styles/` and `dev/`.
- Mobile first: base classes are the smallest supported width; `md:` / `lg:` add the wider layout. Breakpoints come from the ADR's `Viewports:`.

## Conventions

- File names kebab-case; React components PascalCase exports, one component per file; hooks `use-*.ts` exporting `use*`.
- Named exports only (route files excepted, where the framework requires a default).
- Imports through the path alias (`@/features/...`), never `../../..` across features; a feature imports another feature only through its `index.ts`.
- Prettier with a `format:check` script, ESLint with the framework preset plus `import/order` and `no-restricted-imports` for `dev/`; CI runs format → typecheck → lint → tests.
