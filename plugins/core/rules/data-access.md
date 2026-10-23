---
paths:
  - "**/db/**"
  - "**/repository*"
  - "**/repositories/**"
  - "**/migrations/**"
  - "**/drizzle/**"
  - "**/prisma/**"
  - "**/alembic/**"
  - "**/*.sql"
---

# Data access (database)

## Queries

- All SQL for an aggregate lives in its repository. Routes, components and services call repository functions and never build queries.
- Every query on user data takes the owner (`userId`, `tenantId`) as a required argument and filters by it, reads and writes alike. A function that can return another owner's rows is a defect even if no caller passes a foreign id today.
- Parameterised queries or the ORM's builder only. Never concatenate or template user input into SQL.
- No N+1: load a list's relations with a join or one `where id in (…)` batch, never a query per row. Selects name their columns when a table has wide or sensitive ones.
- Multi-step writes that must succeed together run in one transaction. Concurrency (one run at a time, counters, quotas) uses a conditional update (`update … where … returning`) or a row lock, never read-then-write in app code.

## Schema and migrations

- The schema in code (Drizzle, Prisma, SQLAlchemy) is the source. Every change ships as a generated migration in the same commit. Review its SQL and never edit the DB by hand.
- Run `generate` after a change and expect no further drift. An ERD in `docs/erd.md`, if the repo keeps one, changes in the same commit.
- Each table gets a primary key, `created_at` / `updated_at`, foreign keys with an explicit `on delete`, and indexes on every foreign key and every column a hot query filters or sorts by.
- Destructive or long-running changes (drop, rename, type change, backfill on a big table) are a data migration: expand → backfill → switch → contract, never in one step. Use `/write-migration` (ship, if installed).
- Soft delete (`deleted_at`) and retention jobs are explicit decisions: queries exclude deleted rows, and a purge job removes them on schedule.

## Tests

- Repository tests run on a real engine: PGlite or SQLite in-process, or testcontainers. Apply the real migrations and seed. Never mock the database.
- Each repository function has a test that another owner's rows are invisible and untouched, plus its edge cases (empty, duplicate, concurrent).
