---
model: opus
effort: high
name: tdd
description: Drives implementation as a red → green loop — one seam, one failing test, one minimal implementation per cycle. Use when building a feature test-first, when a PLAN.md task has a verify command, or when the user says TDD, test-first, or red-green.
when_to_use: implementing a task from PLAN.md, building a feature where the behaviour is known but the design is not, fixing a bug once /fix-bug has a red loop, or any time tests would otherwise get written after the fact
---

# TDD

The loop is **red → green**. This skill is what makes the loop produce tests worth keeping: where tests go, what a good one is, and the rules that stop the loop degrading into test-shaped busywork.

Every section applies on every cycle. Consult them during the loop, not after.

---

## Before the loop

Read `.claude/docs/test-strategy.md` and `.claude/docs/conventions.md` if they exist — test location, framework, markers, and naming are facts, so they come from there.

Read `.claude/docs/glossary.md` if it exists, so test names use the project's own domain terms. A test called `cancels the order` when the codebase says `void` is a test nobody will find.

---

## Seams — where tests go

A **seam** is the public boundary you test at: the place you observe behaviour without reaching inside.

**Test only at agreed seams.** Before writing the first test, name the seams under test and confirm them with the user:

> "The seams I'd test are `<A>` and `<B>`. Anything else you want covered, or anything here you'd drop?"

You cannot test everything. Agreeing seams up front is how the effort lands on critical paths and complex logic instead of spreading evenly over trivia. No test gets written at an unconfirmed seam.

Record the agreed seams in `specs/<slug>/TEST_MATRIX.md` before the first cycle.

---

## The loop

One cycle = one seam, one test, one minimal implementation.

1. **Red.** Write the failing test. Run it. **Watch it fail**, and read the failure — a test that fails for the wrong reason is not red, it's broken.
2. **Green.** Write only enough code to pass it. No speculative branches, no anticipating the next test.
3. **Record.** Tick the behaviour in `TEST_MATRIX.md`.
4. **Repeat.** The next test responds to what this cycle taught you.

**Completion criterion for a cycle:** the new test passed, every previously passing test still passes, and `TEST_MATRIX.md` has the row.

Refactoring is not part of the loop. It belongs to `/code-review` and `/simplify` after the behaviour is green.

---

## What a good test is

A good test verifies behaviour through a public interface and reads like a specification. `user can checkout with a valid cart` tells you what capability exists. It survives refactors because it never knew the internal structure.

The implementation can change entirely; the test shouldn't.

---

## Anti-patterns

- **Implementation-coupled** — mocks internal collaborators, tests private methods, or asserts through a side channel (querying the DB instead of using the interface). The tell: it breaks on a refactor when behaviour did not change.
- **Tautological** — the assertion recomputes the expected value the way the code does, so it passes by construction and can never disagree with the code. `expect(add(a, b)).toBe(a + b)` is the classic. Expected values must come from an independent source: a known-good literal, a worked example, the spec.
- **Horizontal slicing** — all the tests first, then all the implementation. Bulk tests verify *imagined* behaviour: you commit to a test structure before understanding the implementation, and the tests end up insensitive to real change. Work in **vertical slices** instead — one test, one implementation, repeat.

`rules/testing.md` owns the general rules — what to test, what not to add, granularity, the quality-gate order. This skill owns only the loop and the anti-patterns above.

---

## Where this sits in the chain

```
/writing-plans   → PLAN.md, each task carrying a <verify> command
      ↓
/tdd             → the <verify> command is the red → green target — this skill
      ↓
/code-review     → refactor, simplify, find bugs
      ↓
/checkpoint      → full quality gate
```

A PLAN.md task's `<verify>` field is already a completion criterion. TDD is how you get there: the verify command is what must go from red to green.

`/gen-tests` is the opposite direction — it scaffolds tests for code that already exists, to close a coverage gap. Reach for it on legacy code; reach for `/tdd` when the code has yet to be written.

---

## Hard gates

- **Red before green**, every cycle. A test that has never failed has never been shown to test anything.
- **One slice at a time** — one seam, one test, one minimal implementation.
- **An unconfirmed seam gets no test.** Ask first.
- **Behaviour, not implementation.** If the test needs to reach past the interface, the module is the wrong shape — see `/codebase-design`.
