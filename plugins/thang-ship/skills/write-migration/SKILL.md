---
model: opus
effort: high
name: write-migration
description: Writes or reviews a database/schema migration so it is reversible, non-locking and deployable while old code still runs — expand/contract, backfill separated, down path tested. Use whenever a change adds, renames or drops a table, column, index or constraint, or backfills data. Always high-risk lane.
when_to_use: adding, renaming or dropping a column or table, schema change, backfill, D1/Prisma/Drizzle/Alembic/Knex migration files
---

# write-migration — the scariest change class, made boring

**Invoke:** `/write-migration <what changes>` or point it at an existing migration file to review.

Hard gate: data migration → `high-risk` lane, user confirms before anything runs against a shared database.

## Step 1 — Find the project's migration tool

Read `.claude/docs/stack.md` or look for `migrations/`, `prisma/`, `drizzle/`, `alembic/`, `wrangler d1 migrations`. Copy the newest existing migration's style; never hand-write a format the tool did not generate.

## Step 2 — Shape it as expand → migrate → contract

| Change | Safe shape |
|--------|-----------|
| Add column | Nullable or with default first; make NOT NULL in a later migration after backfill |
| Rename column/table | Add new → dual-write → backfill → switch reads → drop old in a later release. Never a single rename while old code runs |
| Drop column/table | Stop reading/writing in code first (one release), drop afterwards |
| Add index on a big table | Use the DB's non-blocking form (`CONCURRENTLY` on Postgres) |
| Backfill | Separate migration or script, batched, idempotent, resumable |

## Step 3 — Checklist before handing off

- [ ] Old code still works against the new schema (deploy order: migrate, then code)
- [ ] Down/rollback path exists and was run locally: up → down → up
- [ ] No full-table rewrite or long lock on a large table
- [ ] Backfill is batched and safe to re-run
- [ ] Destructive step (drop/truncate) is in its own later migration, and the user confirmed it
- [ ] Test covers the new constraint or the data transformation

## Output

The migration file(s), the deploy order, the exact rollback command, and the checklist with evidence — added to `specs/<slug>/SUMMARY.md` under `## Rollback`.

## Rules

- Never run a migration against a shared/staging/production DB yourself; print the command for the user.
- Never combine schema change and destructive cleanup in one migration.
