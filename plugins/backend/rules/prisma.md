---
paths:
  - "**/prisma/**"
  - "**/*.prisma"
  - "**/db.{ts,js}"
  - "**/prisma.{ts,js}"
---

# Prisma rules

## Migrations

- Change the schema, then `prisma migrate dev --name <what-changed>` locally. CI and production run `prisma migrate deploy` only — never `migrate dev`, `migrate reset` or `db push` against a shared database.
- Commit `schema.prisma` and the new `prisma/migrations/<timestamp>_<name>/` folder in the same commit.
- Never edit a migration that has been applied anywhere; add a new one.
- A rename in the schema is generated as drop + add, which deletes the column's data. Use `prisma migrate dev --create-only`, rewrite the SQL as a rename (or expand/contract for zero downtime), then apply.
- A new required column on a table with rows needs a default or a backfill step before the `NOT NULL`.

## Client

- One `PrismaClient` per process. In Next.js dev, keep it on `globalThis` so hot reload does not open a new pool each time.
- Run `prisma generate` after every schema change; never hand-edit generated client code.
- Multi-write changes go in `prisma.$transaction`; keep interactive transactions short — no network calls inside.

## Queries

- `select` the fields you need; `include` only the relations you read.
- No queries in a loop: fetch related rows with `include`, or one `findMany({ where: { id: { in: ids } } })`.
- Raw SQL only through the `$queryRaw` / `$executeRaw` tagged templates, which parameterize. `$queryRawUnsafe` / `$executeRawUnsafe` never take user input.
- Paginate list endpoints (`take` + cursor); never return an unbounded `findMany`.

## Logging

- Query logging (`log: ['query']`) is for local debugging only — parameters can carry PII and tokens.
