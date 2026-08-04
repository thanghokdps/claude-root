---
model: opus
effort: high
name: fix-bug
description: Diagnosis loop for bugs and performance regressions — build a tight red loop first, then minimise, hypothesise, instrument, fix, and lock it down with a regression test. Use when the user reports something broken, throwing, failing, or slow.
when_to_use: a bug report, a failing test nobody understands, a performance regression, "debug this", "why is this happening", or a symptom with no known cause
---

# fix-bug

**Invoke:** `/fix-bug <symptom>`

Fix only the specific bug. No refactoring, no cleanup, no "while I'm here".

Skip a phase only with an explicit, stated justification.

Read `.claude/docs/architecture.md` and `.claude/docs/glossary.md` if they exist — the mental model comes from there rather than from a cold read of the source.

---

## Phase 1 — Build a tight red loop

**This is the skill.** Everything after it is mechanical.

With a **tight** pass/fail signal that goes **red** on *this* bug, you will find the cause — bisection, hypothesis-testing, and instrumentation all just consume that signal. Without one, no amount of staring at code will save you.

Spend disproportionate effort here. Be aggressive, be creative, refuse to give up.

### Ways to construct one — roughly in this order

1. **Failing test** at whatever seam reaches the bug — unit, integration, e2e.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffed against a known-good snapshot.
4. **Headless browser script** (Playwright/Puppeteer) asserting on DOM, console, or network.
5. **Replay a captured trace** — save a real request/payload/event log, replay it through the code path in isolation.
6. **Throwaway harness** — a minimal subset of the system that hits the bug path in one function call.
7. **Property / fuzz loop** — for "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness** — if it appeared between two known states, automate "boot at state X, check, repeat" so `git bisect run` can drive it.
9. **Differential loop** — same input through old vs new (or two configs), diff the outputs.

### Tighten it

Treat the loop as a product. Once you have *a* loop:

- **Faster?** Cache setup, skip unrelated init, narrow the scope.
- **Sharper signal?** Assert the specific symptom, not "didn't crash".
- **More deterministic?** Pin time, seed RNG, isolate the filesystem, freeze network.

A 30-second flaky loop is barely better than none. A 2-second deterministic one is a superpower.

**Non-deterministic bugs:** the goal is not a clean repro but a **higher reproduction rate**. Loop the trigger 100×, parallelise, add stress, inject sleeps. A 50%-flake bug is debuggable; 1% is not — keep raising the rate.

### Completion criterion

Name **one command** you have **already run at least once** — paste the invocation and its output — that is:

- [ ] **Red-capable** — drives the actual bug path and asserts the user's *exact* symptom, so it goes red now and green once fixed
- [ ] **Deterministic** — same verdict every run (or a pinned high repro rate)
- [ ] **Fast** — seconds, not minutes
- [ ] **Agent-runnable** — you can run it unattended

Catching yourself reading code to build a theory before this command exists means stopping: **jumping to a hypothesis is the exact failure this phase prevents.** No red-capable command, no Phase 2.

**When you genuinely cannot build one**, say so explicitly, list what you tried, and ask for (a) access to an environment that reproduces it, (b) a captured artifact — HAR, log dump, screen recording with timestamps, or (c) permission to add temporary instrumentation. Hypothesising without a loop is off the table.

---

## Phase 2 — Reproduce and minimise

Run the loop. Watch it go red.

- [ ] The failure is the one the **user** described — not a different one nearby. Wrong bug, wrong fix.
- [ ] It reproduces across multiple runs.
- [ ] The exact symptom is captured, so later phases can prove the fix addressed it.

Then **minimise**: shrink to the smallest scenario still going red. Cut inputs, callers, config, data, and steps **one at a time**, re-running after each cut.

Done when every remaining element is load-bearing — removing any one turns the loop green.

A minimal repro shrinks the hypothesis space in Phase 3 and becomes the regression test in Phase 5.

---

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses before testing any of them**. Generating one at a time anchors you on the first plausible idea.

Each must be falsifiable — state its prediction:

> "If `<X>` is the cause, then `<changing Y>` makes the bug disappear."

A hypothesis with no prediction is a vibe. Sharpen it or drop it.

**Show the ranked list to the user before testing.** They often re-rank it instantly ("we deployed a change to #3 yesterday") or have already ruled one out. Cheap checkpoint, big saving. Proceed with your own ranking if they are away.

---

## Phase 4 — Instrument

Each probe maps to a specific prediction from Phase 3. **Change one variable at a time.**

1. **Debugger / REPL** where the environment supports it — one breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix — `[DEBUG-a4f2]` — so cleanup is one grep. Untagged logs survive forever; tagged ones die.

**Performance regressions:** logs are usually the wrong tool. Establish a baseline measurement (timing harness, profiler, query plan), then bisect. Measure first, fix second.

---

## Phase 5 — Fix and lock it down

Write the regression test **before the fix** — if a **correct seam** exists for it.

A correct seam exercises the real bug pattern as it occurs at the call site. A seam too shallow to replicate the chain that triggered the bug gives false confidence instead of coverage.

**No correct seam is itself the finding.** Record it: the architecture is preventing the bug from being locked down. Carry it to Phase 6.

With a correct seam:

1. Turn the minimised repro into a failing test there.
2. Watch it fail.
3. Apply the smallest fix that addresses the root cause.
4. Watch it pass.
5. Re-run the Phase 1 loop against the original, un-minimised scenario.

A fix needing a larger structural change stops here — report it and propose it as a separate `/feature`.

---

## Phase 6 — Clean up, commit, post-mortem

- [ ] Original repro no longer reproduces (re-run the Phase 1 loop)
- [ ] Regression test passes, or the missing seam is documented
- [ ] All `[DEBUG-...]` instrumentation removed — grep the prefix
- [ ] Throwaway harnesses deleted
- [ ] `specs/<slug>/TEST_MATRIX.md` has the new regression row

```bash
git add <only the files the fix needed>
git commit -m "fix: <what was wrong and what fixed it>"
```

State the hypothesis that turned out correct in the commit body, so the next debugger learns from it.

- Good: `fix: prevent double-emit of TOOL_CALL_END when parallel tool calls overlap`
- Bad: `fix: bug in tool call handling`

**Then ask: what would have prevented this bug?** If the answer is architectural — no good test seam, tangled callers, hidden coupling — say so now, with the specifics. Make that recommendation *after* the fix lands; you know more than you did at Phase 1.

If the root cause was genuinely non-obvious, record it via `/compound` so the class of bug does not come back.
