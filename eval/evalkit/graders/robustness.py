"""Tier 5 — robustness: held-out tests the solver never sees.

The FAIL_TO_PASS / PASS_TO_PASS sets in `tests/` are the *visible* contract. A
solver that hardcodes the exact cases in those files scores 1.0 on correctness
while implementing nothing — that is the reward-hacking failure this harness
exists to catch, and execution alone cannot catch it.

`heldout/` is the answer. Those tests are copied into the workspace only *after*
the solver has finished and only for grading, so a hardcoded lookup table built
from the visible tests fails them. Two kinds live there:

  - extra worked examples outside the visible set
  - property tests: invariants that must hold for *generated* inputs, so there
    is no finite set of cases to hardcode

A task with no heldout/ directory is graded `skipped` — it still reports a
correctness score, but it cannot distinguish a real solution from a hardcoded
one, and the report says so.
"""

from __future__ import annotations

import os

from ..models import GraderResult
from .correctness import run_pytest_files


def grade_robustness(task, workdir: str, runner=None) -> GraderResult:
    if not task.heldout:
        return GraderResult(
            "robustness",
            passed=True,
            score=1.0,
            skipped=True,
            details={"reason": "no heldout tests — hardcoded solutions are NOT detectable"},
        )

    passed = run_pytest_files(task.heldout, workdir, runner=runner)
    return GraderResult(
        name="robustness",
        passed=passed,
        score=1.0 if passed else 0.0,
        details={"heldout_files": task.heldout, "passed": passed},
    )


def heldout_dir(task) -> str:
    return os.path.join(task.dir, "heldout")
