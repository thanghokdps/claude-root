---
model: opus
effort: high
name: db-change
description: Adds or changes a table, column, index or relation and the repository queries that read it, the way the repo already does it (hand-written SQL migrations, Drizzle, Prisma, SQLAlchemy/Alembic). It covers the schema in code and the ERD, a new migration file next to the existing ones, owner-scoped repository functions with bound parameters, seed data, and tests on a real engine (PGlite, SQLite, testcontainers). Use whenever a column, table or query is added or changed — one column is enough — when a query is slow or returns another owner's rows, or when the schema and the migrations have drifted.
when_to_use: add a table, "thêm bảng", "thêm cột", add a column to a table, a new field such as cancelled_at or deleted_at, index, foreign key, relation, migration, schema change, a query that returns rows by a new field, repository function, query, N+1, slow query, seed data, drizzle, prisma, alembic, sqlalchemy, "query trả dữ liệu của user khác" — even a one-column change
---

# db-change

**Invoke:** `/db-change <what must be stored or queried>`

Rules: `data-access.md` and `app-structure.md` from core (in `~/.claude/rules/`); with Prisma, `${CLAUDE_PLUGIN_ROOT}/rules/prisma.md`. A destructive or long-running change (drop, rename, type change, backfill on a large table) is a data migration: hand it to `/write-migration` (ship, if installed) and treat it as high-risk.

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| ORM and schema | `drizzle.config.*` + `db/schema/`, `prisma/schema.prisma`, `models.py` + `alembic/` |
| Migrations | `drizzle/`, `prisma/migrations/`, `alembic/versions/`, and the generate/migrate scripts in `package.json` or the Makefile |
| ERD | `docs/erd.md` or similar |
| Repositories | `server/<aggregate>/repository.ts`, `repositories/`, `crud.py` |
| Test DB | PGlite / SQLite helper, testcontainers, the `testDb()`-style helper and its seed |

**Done when:** each row names a file path. The change is classified as **additive** (new table, nullable or defaulted column, index) or **destructive / long-running** → `/write-migration` (ship, if installed).

## Step 2 — Model first

1. Update the ERD (if the repo keeps one): entity, columns with types, keys, relations with `on delete`, and the indexes the queries need.
2. Update the schema in code to match: primary key, `created_at`/`updated_at`, foreign keys, an index on every foreign key and every filtered or sorted column, and an owner column (`user_id`/`tenant_id`) on user data.
3. Generate the migration with the repo's command. **Read the SQL**: no unintended drop or rewrite, defaults safe for existing rows, indexes built without a long lock where the engine needs `concurrently`. Run `generate` again and expect no changes.

**Done when:** the ERD, the schema and the migration agree, and the migration applies cleanly to a fresh test DB and to one with seed data.

## Step 3 — Repository, test first

- One failing test per function, on the real engine with the real migrations: the happy path, **another owner's rows are invisible and untouched**, empty, duplicate or conflict, and concurrent where it matters.
- Then the function: the owner is a required argument and goes into the `where` of every read and write. Use a join or batch instead of a query per row, a transaction for multi-step writes, and a conditional update or lock for counters, quotas and "one at a time".
- Seed data for new tables, if the app has a seed, so dev and the test DB stay usable.

**Done when:** the repository tests pass, plus typecheck and lint.

## Step 4 — Prove it

Run the migration on the local dev database with the repo's script. Show the applied migration and one query of the new data (or `EXPLAIN` for a performance change, before and after).

**Done when:** the migration output and the query result are pasted.

---

Hand-offs: the endpoint that uses it → `/api-endpoint` · a data migration on existing rows → `/write-migration` (ship, if installed) · done → `/verify-done` → `/review-checklist` → `/docs-sync` so the new table or query is in `.claude/docs/` (skip when `/feature` called this skill; it syncs once for the whole feature).
