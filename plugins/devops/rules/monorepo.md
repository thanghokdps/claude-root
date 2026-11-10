---
paths:
  - "**/turbo.json"
  - "**/pnpm-workspace.yaml"
  - "**/package.json"
---

# Monorepo rules (pnpm workspaces + Turborepo)

Layout inside each app is core's `app-structure.md` under `apps/<app>/src`. Claims cite pnpm.io and turborepo.dev (read 2026-11-10).

## Layout

- `apps/*` are deployables (`web`, `api`), `packages/*` are libraries (`shared`). An app never imports another app; anything two apps need moves to a package.
- `packages/shared` holds what both sides must agree on: Zod schemas, DTO types, error codes, event names. Nothing in it imports a framework, a database client or `process.env`.
- The workspace is declared in `pnpm-workspace.yaml` with a `packages` list of globs, and internal dependencies use `workspace:*`, which resolves only to the local package ([workspaces](https://pnpm.io/workspaces)). One lockfile at the root.

## Turborepo

- `turbo.json` declares tasks under `tasks`, for example `build: { dependsOn: ["^build"], outputs: ["dist/**"] }`. `^` waits for the same task in internal dependencies. A task with no `outputs` caches nothing, so declare them for every build ([configuration](https://turborepo.dev/docs/reference/configuration)).
- `lint`, `typecheck` and `test` are tasks too, and the root gate script runs them through `turbo run`, so CI and a laptop run the same thing.
- Environment variables that change a build's output are declared on the task (the `env` key, unverified from memory: check the configuration page before relying on it), so a cache hit never ships a build made for another environment. Production deploys build with the cache off until that is checked.

## Changes across packages

- A change to `packages/shared` runs the typecheck and tests of every app that depends on it in the same PR. A breaking change to a shared schema lands with every caller updated (core's `code-quality.md`).
