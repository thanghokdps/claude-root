# Audit ledger — coverage and findings as data

Read by `/repo-audit` before mapping and after refuting. One run of an audit finds about half of what repeated runs find in total, so every run records what it covered and the next run starts from the gaps instead of re-reading the same files. Adapted from cloudflare/security-audit-skill `RECONNAISSANCE.md` (coverage units, prior-run input), `report-schema.json` and `validate-coverage-ledger.cjs` / `validate-findings.cjs`; cut to the six axes of `/repo-audit` and to two files a person can read.

Both files live under `specs/audit/` in the audited repo. `specs/` is gitignored in user projects, so the ledger is per checkout and never lands in a commit. Validate both after every write:

```bash
python3 -I "${CLAUDE_PLUGIN_ROOT}"/scripts/validate-audit.py specs/audit            # errors as file:id: message, exit 2
python3 -I "${CLAUDE_PLUGIN_ROOT}"/scripts/validate-audit.py specs/audit --summary  # counts per verdict and unit status
```

## `coverage-ledger.json`

```json
{
  "scope": ".",
  "runs": [
    { "run_id": 1, "date": "2026-10-30", "commit": "9f42cb2…(40 hex)", "units_audited": 3 }
  ],
  "units": [
    { "id": "src/billing", "kind": "folder", "path": "src/billing",
      "status": "audited", "last_commit": "9f42cb2…(40 hex)",
      "axes_checked": ["bug", "risk", "scale", "missing_test", "speed", "lean"], "run_id": 1 },
    { "id": "src/api/routes.ts#POST /orders", "kind": "entry_point", "path": "src/api/routes.ts",
      "status": "stale", "last_commit": "0224796…(40 hex)", "axes_checked": ["bug", "risk"], "run_id": 1 },
    { "id": "worker→db", "kind": "trust_boundary", "path": "src/worker/consume.ts",
      "status": "unaudited", "last_commit": null, "axes_checked": [], "run_id": null }
  ]
}
```

| Field | Rule |
|-------|------|
| `scope` | The folder the audit was asked for, repo-relative; `.` for the whole repo |
| `runs[]` | Append-only. `run_id` is 1, 2, 3… in order; `date` is `YYYY-MM-DD`; `commit` is the repo `HEAD` (40 hex) when the run started; `units_audited` is how many units this run set to `audited` |
| `units[].id` | Stable across runs: the path for a folder, `path#symbol or route` for an entry point, `from→to` for a trust boundary. Unique in the file |
| `units[].kind` | `folder`, `entry_point` (main, route, handler, job, CLI command) or `trust_boundary` (where data crosses a process, user, service or storage line) |
| `units[].path` | Repo-relative file or folder; the staleness check runs on it |
| `units[].status` | `unaudited` (never read), `audited` (read on `run_id`, source unchanged since) or `stale` (read, but `git log -1 --format=%H -- <path>` no longer equals `last_commit`) |
| `units[].last_commit` | 40-hex commit of `path` when it was last audited; `null` while `unaudited` |
| `units[].axes_checked` | Which of `bug`, `risk`, `scale`, `missing_test`, `speed`, `lean` were checked on that unit; empty while `unaudited`. A unit checked on two axes is covered on two axes, not six |
| `units[].run_id` | The run that last audited it, present in `runs`; `null` while `unaudited` |

**Units** come from Step 1's map: one per top-level source folder (or per package in a monorepo), one per entry point, one per trust boundary where a mistake costs the most. A big repo stays at folder granularity except on those paths. Never put a line number, a verdict or a severity in a unit.

**Covered** means `status: audited` with the axis in `axes_checked`. A unit whose only findings are `needs_validation` is not covered: the audit could not settle it. `stale` is not covered either.

## `findings.json`

A JSON array, one record per candidate that went through `${CLAUDE_PLUGIN_ROOT}/references/refute.md`, whatever its verdict. Rejected records stay so the next run does not raise the same claim again.

```json
[
  { "id": "billing/close_day.py:utc-day", "verdict": "confirmed", "axis": "bug", "severity": "must",
    "path": "billing/close_day.py", "line": 40,
    "case": "an order at 00:30 Berlin time is billed the day before: today comes from the UTC server clock",
    "fix": "datetime.now(ZoneInfo(\"Europe/Berlin\")).date()",
    "cost_of_skipping": "late orders carry the wrong date and accounting corrects them by hand",
    "commit": "9f42cb2…(40 hex)", "run_id": 1 },
  { "id": "api/orders.ts:replay", "verdict": "needs_validation", "axis": "risk",
    "path": "src/api/orders.ts", "line": 88,
    "case": "a replayed webhook creates a second order when the idempotency key is not enforced upstream",
    "missing_fact": "whether the gateway dedupes by Idempotency-Key — the payments team or the gateway dashboard",
    "commit": "9f42cb2…(40 hex)", "run_id": 1 },
  { "id": "lib/retry.ts:unused", "verdict": "rejected", "axis": "lean",
    "path": "src/lib/retry.ts", "line": 1,
    "case": "retry() has no caller and can be deleted",
    "refuted_by": "src/jobs/sync.ts:14",
    "commit": "9f42cb2…(40 hex)", "run_id": 1 }
]
```

| Field | Rule |
|-------|------|
| `id` | Stable, `^[A-Za-z0-9][A-Za-z0-9._:/@+-]*$`, unique in the file; derive it from the source (`path:what`), never from the run or the verdict, so the same claim keeps its id across runs |
| `verdict` | `confirmed`, `needs_validation` or `rejected` — from refute.md, nothing else |
| `axis` | `bug`, `risk`, `scale`, `missing_test`, `speed`, `lean` — the row of Step 2's table |
| `severity` | `must`, `should`, `nice`. Required when `confirmed`, forbidden otherwise: refute.md gives an unsettled finding no severity |
| `path`, `line` | Repo-relative file and 1-based line of the cited code |
| `case` | The concrete input or situation and the wrong result |
| `fix`, `cost_of_skipping` | Required when `confirmed`; may be present on `needs_validation` |
| `missing_fact` | Required when `needs_validation`: the fact and who or what answers it |
| `refuted_by` | Required when `rejected`: the refuting `path:line` |
| `commit` | 40-hex `git log -1 --format=%H -- <path>` at the time of the verdict: a later run compares it to decide whether to re-validate |
| `run_id` | The run that produced this verdict; must exist in the ledger's `runs` |

## Across runs

1. **Read both files before mapping.** No files: this is run 1, every unit starts `unaudited`. A file that does not validate is reported, not treated as empty: fix it or ask the user before the audit continues.
2. **Mark stale.** For every `audited` unit, run `git log -1 --format=%H -- <path>`; a different hash sets `status: stale`.
3. **Order the work:** `unaudited` first, then `stale`, then `audited` units checked on fewer than six axes. An `audited` unit on all six axes is read again only when a finding leads there.
4. **Carry findings forward.** A `confirmed` finding whose `commit` still equals `git log -1 --format=%H -- <path>` is carried into the report unchanged, counted under the run that found it. One whose file changed goes back through refute.md as a candidate; it keeps its `id`. A `needs_validation` finding is re-checked every run while its missing fact is still unknown. A `rejected` finding is raised again only when the cited lines changed.
5. **Write after refute.** Append the run to `runs`, set each unit this run read to `audited` with its `last_commit`, `axes_checked` and `run_id`, write every verdict to `findings.json`, then run the validator and fix every error before the report.
6. **Report coverage:** units audited this run / total, stale units left, and `Run N; previous runs: 1 (date), 2 (date)`.
