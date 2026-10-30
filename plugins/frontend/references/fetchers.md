# Frontend → own backend — read by ui-feature Step 3 when the screen calls the app's API

Where it lives: `features/<f>/api.ts`, through the repo's shared `fetchJson`-style helper and its caching library (TanStack Query / SWR). A second helper or a second client for the same endpoint is a defect.

- One typed function per endpoint in the feature's `api.ts`, through the shared helper. Request and response types are **imported** from the backend schema (`server/<aggregate>/schema.ts` or a shared package), never re-declared. A missing export is a contract gap: ask the backend engineer for it, do not copy the shape.
- The helper turns non-2xx into a typed error carrying the backend's `error` code. The UI switches on the code (`not_found`, `quota_exceeded`) and never parses messages.
- Use the repo's caching library (keys, invalidation after a write). Without one, refetch after a successful write rather than patching scattered state.
- Tests mock at the fetch boundary and cover the success shape, an error code, and a network failure.

A third-party API the browser calls directly (maps, analytics, payments widget) is still frontend; one the server calls is `/api-client` (backend, if installed).
