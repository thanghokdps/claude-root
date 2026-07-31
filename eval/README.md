# evalkit — evaluate code an AI agent generates

A small, self-contained harness for the question *"is the code the agent produced
actually correct and up to standard?"* It grades agent output on five tiers and
caches the expensive LLM-judge calls so debug re-runs don't burn tokens.

## Why

Passing tests is necessary but **not sufficient**. A large share of "solved" cases
on public benchmarks pass by luck or by reward-hacking the harness. Concretely,
this solver passes every visible test for the `discount` task and implements
nothing:

```python
def apply_discount(price, pct):
    table = {(100, 10): 90, (50, 50): 25, (100, 0): 100, (80, 25): 60}
    return table[(price, pct)]
```

Execution alone cannot reject it — the tests it must satisfy are a finite, knowable
set. Two mechanisms here can:

- **Held-out tests** (`heldout/`) are copied into the workspace only *after* the
  solver has finished, so they are not a set the solver can enumerate.
- **Property tests** assert invariants over *generated* inputs, so there is no
  finite set of cases to hardcode at all.

A task with no `heldout/` suite is reported as such — the run says plainly that it
cannot tell a real solution from a hardcoded one.

## Grading tiers

| Tier | Grader | Signal | Counts toward `solved`? |
|------|--------|--------|--------------------------|
| 1 | `correctness` | pytest: FAIL_TO_PASS + PASS_TO_PASS (SWE-bench style) | yes |
| 2 | `robustness` | held-out + property tests the solver never sees | yes |
| 3 | `feature` | LLM-as-judge vs. the task rubric, cached via a cassette | no |
| 4 | `quality` | ruff lint + max-nesting + test-gap probe (static) | no |
| 5 | `security` | pattern-based SAST (static) | no |

`solved = correctness AND robustness`. The static tiers report but do not gate —
they describe the code, they don't decide whether the task was done.

## Honest limitations

Read this before quoting a number from this harness.

- **The stub judge is not a judge.** `StubJudge` is an offline keyword heuristic
  that runs with no API key. Its scores are marked **advisory** and are excluded
  from tier averages and from the `solved` verdict. It errs toward `0.0`, which is
  the safe direction for a placeholder. For a real signal use `--judge anthropic`.
- **Test-gap is a reference check, not coverage.** A test file mentioning a symbol
  is not proof the behaviour is covered.
- **Without ruff the quality tier is advisory too** — only the nesting heuristic
  runs, and almost nothing fails it.
- **Two golden tasks is a demo, not a benchmark.** `pass@1` over two tasks carries
  no statistical weight. Use `--repeat K` and read `pass@K`; add tasks before
  drawing conclusions.
- **Held-out tests raise the cost of hardcoding, they don't make it impossible.**
  A sufficiently determined solver could infer the properties. They are a strong
  filter, not a proof of correctness.

## Sandboxing

The code under evaluation was written by an agent, which makes it untrusted. Both
the solver command and pytest execute it, so both run in a throwaway container
with `--network none`, and neither ever sees the operator's environment — the env
is rebuilt from an allowlist, so `ANTHROPIC_API_KEY` and friends never cross the
boundary.

```bash
docker build -t evalkit-sandbox .     # once
python -m evalkit.cli run             # --sandbox auto (default) picks it up
```

Running unsandboxed requires saying so twice, on purpose:

```bash
python -m evalkit.cli run --sandbox none --allow-unsandboxed
```

## Layout

```
eval/
  Dockerfile               # sandbox image (pytest baked in — the container has no egress)
  evalkit/                 # the harness
    runner.py              # load tasks -> solve -> grade  (ordering is load-bearing)
    sandbox.py             # Docker/local runners + environment scrubbing
    judges.py              # AnthropicJudge (real) | StubJudge (offline placeholder)
    cassette.py            # record/replay cache for the judge
    solvers.py             # ReferenceSolver | CommandSolver (plug your agent)
    graders/               # correctness, robustness, feature, quality, security
    report.py  cli.py
  tasks/<id>/              # one golden task each
    task.yaml              # prompt, tests, rubric, symbols
    workspace/             # starting state (empty for greenfield, buggy for bugfix)
    reference/             # known-good solution (upper bound / harness self-check)
    tests/                 # visible graded tests   — copied in after the solver runs
    heldout/               # hidden graded tests    — copied in after the solver runs
  tests/                   # self-tests for the harness
```

The solver runs against a workspace containing **no test files at all**; every
grading fixture is copied in afterwards. That ordering is what stops a solver from
reading the assertions it is about to be graded on.

## Run

```bash
cd eval
pip install -r requirements.txt
docker build -t evalkit-sandbox .

# 1. verify the harness itself
python -m pytest tests/ -q

# 2. run the suite with the reference solver (upper bound — should be 100%)
python -m evalkit.cli run

# 3. five attempts per task, real judge, CI gate at 80%
python -m evalkit.cli run --repeat 5 --judge anthropic --min-pass-rate 0.8

# 4. plug your real agent: it gets $TASK_PROMPT and $WORK_DIR, writes into $WORK_DIR
python -m evalkit.cli run --solver command --command 'claude -p "$TASK_PROMPT"'
```

Reports land in `eval/reports/latest.md` and `latest.json`.

**Exit codes:** `0` on completion, `1` on a usage error, `2` only when
`--min-pass-rate` is set and `pass@1` falls below it. There is deliberately no
"must be 100%" gate — against a real agent that fails every run, and a gate that
always fails stops being read.

## Scoring

- **Denominator excludes invalid tasks.** If FAIL_TO_PASS already passes on the
  untouched workspace, the task measures nothing. That is a benchmark authoring
  bug, and charging it to the solver would report it as a capability failure.
  Such tasks are listed separately as `⚠️ invalid`.
- **`pass@1`** is the mean success rate per attempt — the honest single-shot number.
- **`pass@K`** (with `--repeat K`) counts a task solved if any attempt solved it.
  Agents are stochastic; one sample is an anecdote.

## Add a task

Create `tasks/<id>/` with `task.yaml`, `workspace/`, `reference/`, `tests/`, and
`heldout/`. `mode` is validated against the fixtures: `bugfix` requires a non-empty
workspace, `greenfield` requires an empty one.

Write the held-out suite to defeat a hardcoded solution specifically: include cases
outside the visible set, and at least one property test over seeded random inputs.
Seed the RNG so a failure reproduces.

## Plug a real LLM judge

```bash
pip install anthropic
export ANTHROPIC_API_KEY=...            # or: ant auth login
python -m evalkit.cli run --judge anthropic
```

`AnthropicJudge` calls the Messages API with a JSON schema (`output_config.format`),
so the response is guaranteed parseable rather than prompted-and-hoped-for. It is
instructed to treat comments and docstrings as non-evidence, and to reject a
hardcoded lookup table as unsatisfying a computed-behaviour criterion. Every
judgment is recorded in the cassette, so re-runs are free and deterministic.

Model defaults to `claude-opus-5`; override with `EVALKIT_JUDGE_MODEL`.
