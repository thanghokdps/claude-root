---
type: llm
focus: trace
---

Judge the files the run wrote, attempted or proposed; an attempted Edit or Write counts even when the sandbox denied it. The repo has `migrations/0001_create_orders.py` (Alembic style) and `app/models.py`.

PASS if there is a new migration file (revision `0002`, `down_revision = "0001"`) that adds `cancelled_at` as a nullable column with a working `downgrade`, and `app/models.py` gains the matching field.
FAIL if the column is added only in the model with no migration, if migration 0001 is edited in place, or if the new column is NOT NULL without a default on an existing table.
