---
model: opus
effort: high
name: repo-audit
description: Audits a whole repo or a named folder the way a senior developer who just inherited it would — bugs, security and data-loss risks, what breaks at the expected load, risky code without a test, real slowness, and code to delete, reuse or merge. Returns at most 20 numbered findings in Must / Should / Nice, each with the concrete failing case, the fix and the cost of skipping it. Read-only, one-shot. Use when taking over a codebase or before a big change to it; for a diff or PR use review-checklist instead.
when_to_use: audit this codebase, review the whole repo, inherited or legacy codebase, "audit repo", "rà soát toàn bộ repo", "đánh giá codebase", what can I delete, find bloat, health check before a rewrite or scale-up, /repo-audit
---

# repo-audit — the whole repo, as the next person paged for it

**Invoke:** `/repo-audit [folder | package]` — default: the whole repo.

A diff review sees what changed; this sees what is already there. Order of importance: correct, safe, holds at the expected load, tested, fast, lean. Reads and reports only; changes no code.

## Step 1 — Map first

- Read `.claude/docs/index.md` and what it links when it exists — it is the map; skip what it already answers. Otherwise read the README, manifests, deploy and CI config, entry points (main, routes, handlers, jobs, CLI) and the test layout.
- **Expected load:** one person running a script, or many users and processes at once (README, deploy config, replicas, queues). Scale findings are judged against it; state the load you assumed.
- **Trace the main flows end to end:** where data comes in, what is stored, what goes out. Read fully the paths where a mistake costs the most: user input, money, auth, data writes, background jobs, state shared between processes.
- **Big repo** (more than a few hundred source files): go deep on those paths, not file by file. Mapping many folders may go to `Explore` subagents on `haiku`, one per area, reporting paths and entry points only; every finding is still read and verified here.

**Done when:** you can say in two or three sentences what the repo does, for whom, at what load — and you have listed which parts you did not read.

## Step 2 — Look for

| # | Kind | What it looks like |
|---|------|--------------------|
| 1 | **Bug** | Wrong result or crash; a missed edge case (empty, zero, last item, rounding, time zones); callers that disagree with what a function returns; the same rule applied differently in two places |
| 2 | **Risk** | Injection, missing authz on a mutating path, weak randomness, secrets in code, unvalidated input at a boundary; data loss — swallowed errors, writes in the wrong order, no transaction |
| 3 | **Scale** | Fine for one user, wrong at the expected load: check-then-write races, a query per item, lists or caches that only grow, the same work in every process, per-process state that must be shared |
| 4 | **Missing test** | Risky logic (a branch, a parser, money, security, data writes) with no test that fails when it breaks — one good test, not coverage |
| 5 | **Speed** | A real slowdown is a finding; a small win in a hot loop is Nice |
| 6 | **Lean** | Dead code, unused options and config, speculative features; two helpers doing one job (name the one to keep); a dependency the platform or a few lines replace; an interface with one implementation or a wrapper that only forwards; near-copies that must change together; one function doing unrelated jobs (split by job, never by line count) |

A comment `shortcut: <limit>, <when to upgrade>` is a decision, not a finding — unless the expected load already crosses its limit. `/debt-ledger` lists them.

## Step 3 — Check before you report

- **No concrete case, no finding:** "this input or situation leads to this wrong result". Re-read the lines and confirm the caller exists, the value can really be empty, the path is really reachable.
- Before calling code unused, grep the whole tree for it — tests, fixtures, config, string and dynamic references.
- Run what is cheap to run (the test suite, a one-line repro); mark a finding you could not run as unverified.
- Propose the smallest fix that works; prefer one that deletes code. Never propose a layer, framework or config the problem does not need.
- No style taste, no "consider", no vague worries.

Then send every candidate through `${CLAUDE_PLUGIN_ROOT}/references/refute.md`. The Must / Should / Nice groups hold only `confirmed` findings. List `needs_validation` findings under **Needs validation** (the missing fact and who answers it, no group) and count the `rejected` ones on a `Rejected:` line.

**Done when:** every finding has its case and a verdict, and each "unused" claim has the grep that proves it.

## Output

Plain words; explain a technical term the first time it appears — the reader may never have seen this code. Number findings across all groups, so the user can say "fix 2 and 5". At most 20; if smaller ones were left out, say how many.

```markdown
## Repo audit — <repo or folder>
What this repo does: <two or three sentences>. Load assumed: <one line>.

### Must fix (bug, security, data loss, breaks at the expected load)
1. **Orders land on the wrong day** (`billing/close_day.py:40`)
   - **What this is:** the midnight job that closes the day and bills its orders.
   - **Problem:** "today" comes from the UTC server clock, so an order at 00:30 Berlin time is billed the day before.
   - **Fix:** take the day in the shop's time zone: `datetime.now(ZoneInfo("Europe/Berlin")).date()`.
   - **If skipped:** late orders carry the wrong date and accounting corrects them by hand.

### Should fix (risky code without a test, real slowness, duplication, code that should not exist)
### Nice to have (small speed-ups, shorter forms)
### Needs validation (the missing fact and who answers it)

Rejected: <N, each with its refuting path:line>

Verdict: <healthy | fix 1 and 3 first>
Lean: -<N> lines, -<M> dependencies possible   ← only when lean findings exist
Not checked: <parts not read or not run>
```

Skip empty groups. Nothing found: `What this repo does:`, then `Healthy. Nothing to fix.` and one line on what you checked.

## Hand-offs

A finding to fix → `/fix-bug` for a bug, `/feature` for a larger change (dev, if installed) · security findings → built-in `/security-review` · what a fix would break → `/blast-radius` · deliberate shortcuts → `/debt-ledger` · no `.claude/docs/` yet → `/project-init` (core, if installed), so the next audit starts from the map.
