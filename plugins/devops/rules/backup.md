---
paths:
  - "**/backup/**"
  - "**/scripts/*backup*"
  - "**/scripts/*restore*"
---

# Backup and restore rules

A backup that was never restored is a hope, not a backup. Claims cite firebase.google.com and developers.cloudflare.com (read 2026-11-10).

## Per store

- **Firestore:** turn on point-in-time recovery (7 days instead of 1 hour, [PITR](https://firebase.google.com/docs/firestore/use-pitr)) and a scheduled backup (one daily and one weekly schedule per database, kept up to 14 weeks; restore writes to a new database; Blaze plan, [backups](https://firebase.google.com/docs/firestore/backups)). For a copy outside Google, `gcloud firestore export gs://<bucket>` costs one read per document ([export and import](https://firebase.google.com/docs/firestore/manage-data/export-import)); budget it.
- **D1:** Time Travel restores to any minute in the last 30 days on Workers Paid with `wrangler d1 time-travel restore <db> --timestamp=<unix>`, in place ([Time Travel](https://developers.cloudflare.com/d1/reference/time-travel/)). An off-platform copy uses `wrangler d1 export <db> --remote --output=<file>`, which fails on virtual tables such as FTS5 and blocks other requests while it runs ([import and export](https://developers.cloudflare.com/d1/best-practices/import-export-data/)): export the source tables and rebuild the index on restore, at a quiet hour.
- **R2:** the docs describe lifecycle rules but no versioning or backup feature ([object lifecycles](https://developers.cloudflare.com/r2/buckets/object-lifecycles/)), so a deleted object is gone. Copy objects to a second bucket or provider on a schedule, and keep deletes delayed (soft-delete, then a purge job) where retention allows.

## Every backup plan states

- The recovery point (how much data may be lost) and recovery time (how long until service is back) the spec asks for, and which mechanism meets each.
- Where copies live (another account, region or provider than the data), who can read them, and that they are encrypted.
- How long they are kept, and that retention-deleted data disappears from backups within that window. Say this in the product's retention text.

## The restore drill

- Restore on a schedule (monthly, or what the spec says) into a separate environment, never over production: data, then search index, then files. Time it.
- Check the result with a script: row and document counts, a sample of messages readable, a sample file downloadable, the index answers a known query.
- Write the date, duration, counts and any failure in the runbook. A failed drill is an incident (`/incident`, ship, if installed).
