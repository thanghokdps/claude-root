"""Command-line entry point.

Run from the eval/ directory:

    python -m evalkit.cli run                        # reference solver (upper bound)
    python -m evalkit.cli run --repeat 5             # pass@5 instead of one sample
    python -m evalkit.cli run --judge anthropic      # real LLM judge, not the stub
    python -m evalkit.cli run --solver command \\
        --command "claude -p \\"$TASK_PROMPT\\""       # plug your real agent

Agent-generated code is untrusted, so runs are sandboxed by default. Build the
image once with `docker build -t evalkit-sandbox .`, or opt out explicitly with
`--sandbox none --allow-unsandboxed`.
"""

from __future__ import annotations

import argparse
import os
import sys

from .cassette import Cassette
from .judges import build_judge
from .report import summarize, to_json, to_markdown
from .runner import evaluate_all, load_tasks
from .sandbox import build_runner
from .solvers import CommandSolver, ReferenceSolver

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_IMAGE = "evalkit-sandbox"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="evalkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="run the eval suite")
    run.add_argument("--tasks", default=os.path.join(ROOT, "tasks"))
    run.add_argument("--solver", choices=["reference", "command"], default="reference")
    run.add_argument("--command", help="shell command for --solver command")
    run.add_argument("--judge", choices=["stub", "anthropic"], default="stub",
                     help="stub is an offline heuristic; its scores are advisory only")
    run.add_argument("--repeat", type=int, default=1, metavar="K",
                     help="attempts per task; reports pass@K (agents are stochastic)")
    run.add_argument("--sandbox", choices=["auto", "docker", "none"], default="auto",
                     help="isolation for solver + test execution (default: auto)")
    run.add_argument("--docker-image", default=DEFAULT_IMAGE)
    run.add_argument("--allow-unsandboxed", action="store_true",
                     help="permit running untrusted generated code directly on this host")
    run.add_argument("--cassette", default=os.path.join(ROOT, "reports", "cassette.json"))
    run.add_argument("--no-cache", action="store_true", help="disable the judge cassette")
    run.add_argument("--out", default=os.path.join(ROOT, "reports"))
    run.add_argument("--min-pass-rate", type=float, default=None, metavar="RATE",
                     help="exit non-zero if pass@1 falls below RATE (0.0-1.0). "
                          "Without it the run always exits 0 on completion.")

    args = parser.parse_args(argv)
    if args.cmd == "run":
        return _run(args)
    return 1


def _run(args) -> int:
    if args.repeat < 1:
        print("--repeat must be >= 1", file=sys.stderr)
        return 1

    tasks = load_tasks(args.tasks)
    if not tasks:
        print(f"No tasks found in {args.tasks}", file=sys.stderr)
        return 1

    runner = build_runner(args.sandbox, args.docker_image, args.allow_unsandboxed, ROOT)

    if args.solver == "command":
        if not args.command:
            print("--solver command requires --command", file=sys.stderr)
            return 1
        solver = CommandSolver(args.command, runner=runner)
    else:
        solver = ReferenceSolver()

    if not runner.sandboxed:
        print("WARNING: running agent-generated code unsandboxed on this host.\n",
              file=sys.stderr)

    judge = build_judge(args.judge)
    cassette = Cassette(args.cassette, enabled=not args.no_cache)
    results = evaluate_all(tasks, solver, judge=judge, cassette=cassette,
                           runner=runner, repeat=args.repeat)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "latest.json"), "w", encoding="utf-8") as fh:
        fh.write(to_json(results))
    md = to_markdown(results)
    with open(os.path.join(args.out, "latest.md"), "w", encoding="utf-8") as fh:
        fh.write(md)

    print(md)
    s = summarize(results)
    print(f"sandbox: {runner.name} · judge: {judge.name} · "
          f"cassette: {cassette.hits} hits / {cassette.misses} misses")

    # A gate needs a threshold, not perfection: with a real agent, demanding 100%
    # means the gate fails on every run and stops being read.
    if args.min_pass_rate is not None and s["pass_at_1"] < args.min_pass_rate:
        print(f"FAIL: pass@1 {s['pass_at_1']:.3f} < --min-pass-rate {args.min_pass_rate:.3f}",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
