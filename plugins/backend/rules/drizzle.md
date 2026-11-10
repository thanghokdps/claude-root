---
paths:
  - "**/drizzle/**"
  - "**/drizzle.config.*"
  - "**/db/schema/**"
  - "**/db/schema.ts"
---

# Drizzle rules

Adds only what is Drizzle-specific. Owner scoping, N+1, transactions and the migration workflow in general are in core's `data-access.md`. Claims below cite orm.drizzle.team (read 2026-11-09). The sections up to § Tests are written for Postgres. On SQLite and Cloudflare D1, § SQLite and Cloudflare D1 replaces their client, transaction, search and migrate rules.

## Schema and migrations

- The TypeScript schema under `db/schema/` is the source; the database follows it ([migrations](https://orm.drizzle.team/docs/migrations): "codebase first", the schema "is a source of truth"). One file per aggregate (`db/schema/channels.ts`), re-exported from `db/schema/index.ts`, which `drizzle.config.*` points at.
- After every schema change run `drizzle-kit generate --name <what-changed>` and commit the new `drizzle/<timestamp>_<name>/` folder (its `migration.sql` and snapshot) in the same commit as the schema ([generate](https://orm.drizzle.team/docs/drizzle-kit-generate)). Read the SQL before committing: an unexpected `DROP` or `ALTER … TYPE` is a defect, not a surprise to fix in prod.
- Migrations are add-only. Never edit or delete a migration folder once it is on `main`; fix forward with a new one. SQL that drizzle-kit cannot express (`CREATE EXTENSION unaccent`, a function, a trigger, a backfill) goes in `drizzle-kit generate --custom --name <what>` ([generate](https://orm.drizzle.team/docs/drizzle-kit-generate): `--custom` creates an empty migration for hand-written SQL).
- CI and production apply migrations with `drizzle-kit migrate` (or the programmatic equivalent at deploy time), which records each applied file in `drizzle.__drizzle_migrations` ([migrate](https://orm.drizzle.team/docs/drizzle-kit-migrate)). `drizzle-kit push` is for a throwaway local database only: it diffs and applies without a migration file, so nothing is reviewed or replayable, and `--force` auto-accepts data-loss statements ([push](https://orm.drizzle.team/docs/drizzle-kit-push)). Never run `push` against a shared, staging or production database.
- Destructive or long-running changes (drop, rename, type change, backfill of a big table) go through `/write-migration` (ship, if installed), as `data-access.md` says.

## Tables

- Every table: a primary key, `created_at` / `updated_at` with `defaultNow()`, foreign keys with `.references(() => parent.id, { onDelete: '…' })` chosen explicitly, and user data carries its owner key (`user_id`, `workspace_id`).
- Indexes are declared in the table's extras callback (third `pgTable` argument) — `index('messages_channel_id_idx').on(t.channelId)` — on every foreign key and on every column a hot query filters or sorts by; `uniqueIndex` for natural keys ([indexes & constraints](https://orm.drizzle.team/docs/indexes-constraints)). Declaring the index in the schema is what makes `generate` emit it; an index added by hand to the database drifts.
- Full-text search: Postgres has no Drizzle type for `tsvector`, so the search column or expression and its GIN index are declared with `sql`, for example ``index('messages_search_idx').using('gin', sql`to_tsvector('simple', unaccent(${t.body}))`)`` ([postgresql full-text search](https://orm.drizzle.team/docs/guides/postgresql-full-text-search)). The `unaccent` extension and any immutable wrapper function it needs come from a `--custom` migration committed before the index that uses them.

## Client

- One `pg` `Pool` per process, created once in the db module and passed as `drizzle({ client: pool })` ([node-postgres setup](https://orm.drizzle.team/docs/get-started-postgresql): the "existing driver" form). Every request, job and test shares that `db`; `pool.end()` runs on shutdown and in `afterAll`.
- `drizzle-kit` reads `DATABASE_URL` from `drizzle.config.*`; the app reads it through its validated config, never both from different variables.

## Queries

- Use the query builder; where raw SQL is needed, only the `` sql`…` `` tagged template, which binds `${value}` as `$n` parameters and escapes `${table.column}` as identifiers ([sql operator](https://orm.drizzle.team/docs/sql): dynamic parameters "will be mapped to the $1 placeholder"). `sql.raw()` inserts text unescaped and never takes anything derived from user input ([sql operator](https://orm.drizzle.team/docs/sql)).
- Repository functions take the owner as a required argument and put it in every `where`, for reads and writes alike, e.g. `and(eq(messages.id, id), eq(messages.workspaceId, workspaceId))`; a `delete` or `update` by id alone is a defect (`data-access.md`).
- Select the columns you return: `db.select({ id: t.id, … })` rather than the whole row when a table has wide or sensitive columns; the DTO is built from that, never from `SELECT *`.
- Multi-step writes run in `db.transaction(async (tx) => …)` and use `tx` for every statement inside; a thrown error (or `tx.rollback()`) rolls the whole unit back ([transactions](https://orm.drizzle.team/docs/transactions)). Keep transactions short — no network call inside.
- Lists: `.limit(n)` with a server maximum, a stable `orderBy` (`created_at`, then `id`), and a cursor or offset (`api-contract.md`).

## Tests

- Repository tests run on a real Postgres migrated with the committed `drizzle/` folder (`drizzle-kit migrate` or the programmatic migrator against the test database), never PGlite-only when the schema uses `unaccent`, FTS or other Postgres extensions. A test per function proves another owner's rows are invisible and untouched.

## SQLite and Cloudflare D1

The platform side (limits, bindings, environments) is in `cloudflare-workers.md`. Claims cite orm.drizzle.team and developers.cloudflare.com/d1 (read 2026-11-10).

- Tables use `sqliteTable` from `drizzle-orm/sqlite-core`. The client is `drizzle(env.DB)` from `drizzle-orm/d1`, built from the request's binding ([Drizzle + D1](https://orm.drizzle.team/docs/connect-cloudflare-d1)) and passed to the repository. Never keep it in a module-level global.
- An atomic multi-step write is one `db.batch([...])`. D1 runs a batch as a SQL transaction and rolls the whole sequence back when a statement fails ([D1 database API](https://developers.cloudflare.com/d1/worker-api/d1-database/)). Drizzle supports batch on D1 ([SQLite batch API](https://orm.drizzle.team/docs/sqlite/batch-api)). Every statement is built before the batch runs, so one statement cannot use another's result in JavaScript. Write the condition into the SQL instead: `INSERT … SELECT … WHERE NOT EXISTS`, `INSERT … ON CONFLICT DO NOTHING`, or an `UPDATE … WHERE` that a later statement depends on.
- Pick the column types once and keep them across the schema. Ids are app-generated text (UUIDv7) unless a table needs an integer sequence. Timestamps are integer milliseconds. Enums are `text` with a `CHECK`. Booleans are `integer` 0/1.
- Migrations: `drizzle-kit generate` writes one folder per migration. Point the D1 binding at it with `migrations_dir` and `"migrations_pattern": "<dir>/*/migration.sql"` ([D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/)). Apply with `wrangler d1 migrations apply <db> --env <env> --remote`, which records each file in `d1_migrations` ([D1 migrations](https://developers.cloudflare.com/d1/reference/migrations/)). Not `drizzle-kit migrate` and never `push`. Add-only and reviewed, as § Schema and migrations says.
- Full-text search: D1 ships the FTS5 module ([D1 SQL statements](https://developers.cloudflare.com/d1/sql-api/sql-statements/)). The `CREATE VIRTUAL TABLE … USING fts5` and the triggers that keep it in sync go in a `drizzle-kit generate --custom` migration. Index a folded column (lower-case, diacritics stripped) that one shared function produces for both writes and queries. Always join to the conversations the caller belongs to, never search the whole table and filter afterwards.
- Tests run on local D1 inside `@cloudflare/vitest-plugin`, with the committed migrations applied (`cloudflare-workers.md` § Tests), never on a Node SQLite stand-in that lacks D1's behaviour.
