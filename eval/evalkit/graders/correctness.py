"""Tier 1 — execution-based correctness (the gold standard).

Mirrors SWE-bench's two test sets:
  FAIL_TO_PASS — must FAIL before the fix and PASS after (proves the task was done)
  PASS_TO_PASS — must PASS after (proves nothing else was broken)

`grade_correctness` runs both against the solved workspace. The runner separately
runs FAIL_TO_PASS against the *untouched* workspace to catch the "lucky pass"
problem: a test that already passes with no solution is not measuring anything.

Passing both sets is necessary but not sufficient. Their contents are knowable,
so they can be satisfied by hardcoding the cases rather than implementing the
behaviour — that is what graders/robustness.py exists to catch.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

from ..models import GraderResult
from ..sandbox import LocalRunner

_HOST_PYTEST = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
_CONTAINER_PYTEST = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]


def run_pytest_files(files: list[str], workdir: str, timeout: int = 120, runner=None) -> bool:
    """Return True iff every listed test file passes (pytest exit code 0)."""
    if not files:
        return True
    runner = runner or LocalRunner()
    base = _CONTAINER_PYTEST if getattr(runner, "sandboxed", False) else _HOST_PYTEST
    try:
        proc = runner.run([*base, *files], workdir=workdir, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return proc.returncode == 0


def grade_correctness(task, workdir: str, runner=None) -> GraderResult:
    f2p = run_pytest_files(task.fail_to_pass, workdir, runner=runner)
    p2p = run_pytest_files(task.pass_to_pass, workdir, runner=runner)
    passed = f2p and p2p
    # Score = fraction of the two test sets that pass (both weighted equally).
    parts = []
    if task.fail_to_pass:
        parts.append(1.0 if f2p else 0.0)
    if task.pass_to_pass:
        parts.append(1.0 if p2p else 0.0)
    score = sum(parts) / len(parts) if parts else 0.0
    return GraderResult(
        name="correctness",
        passed=passed,
        score=score,
        details={"fail_to_pass": f2p, "pass_to_pass": p2p},
    )


def find_test_references(symbols: list[str], workdir: str) -> dict:
    """Which of `symbols` are referenced by at least one test file under `workdir`.

    This backs the quality tier's test-gap signal. It is a *reference* check, not
    a coverage measurement: a test file mentioning a symbol is not proof the
    behaviour is covered. Callers must report it as such.
    """
    referenced: dict[str, list[str]] = {s: [] for s in symbols}
    if not symbols:
        return referenced
    patterns = {s: re.compile(rf"\b{re.escape(s)}\b") for s in symbols}
    for root, _dirs, files in os.walk(workdir):
        for name in files:
            if not _looks_like_test(name):
                continue
            path = os.path.join(root, name)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for symbol, pattern in patterns.items():
                if pattern.search(text):
                    referenced[symbol].append(os.path.relpath(path, workdir))
    return referenced


def _looks_like_test(name: str) -> bool:
    return (
        name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
    )
