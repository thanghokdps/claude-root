"""Tier 3 — static code quality: lint (ruff), nesting depth, and a test-gap probe.

Deterministic and cheap. If ruff is not installed the lint sub-check is skipped —
but the whole tier is then marked **advisory**, because the remaining nesting
heuristic passes almost everything and a bare 1.00 would look like a verdict it
has not earned. Install ruff (it is in requirements.txt) to get a real score.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess

from ..models import GraderResult
from .correctness import find_test_references

MAX_NESTING = 4  # depth beyond this is flagged as too deeply nested


def grade_quality(task, workdir: str) -> GraderResult:
    files = [f for f in task.target_files if f.endswith(".py")]
    abs_files = [os.path.join(workdir, f) for f in files if os.path.exists(os.path.join(workdir, f))]
    if not abs_files:
        return GraderResult("quality", passed=True, score=1.0, skipped=True,
                            details={"reason": "no target python files found"})

    lint_ok, lint_info = _ruff(abs_files, workdir)
    deep = _max_nesting(abs_files)
    nesting_ok = deep <= MAX_NESTING
    tested, test_info = _test_gap(task, workdir)

    checks = [c for c in (lint_ok, nesting_ok, tested) if c is not None]
    score = sum(1.0 for c in checks if c) / len(checks) if checks else 1.0

    # With ruff absent only the nesting heuristic runs, which almost nothing
    # fails — a 1.00 from one weak check would read as "quality verified".
    # Mark it advisory so it is reported but never counted.
    advisory = lint_ok is None
    return GraderResult(
        name="quality",
        passed=all(c for c in checks),
        score=score,
        advisory=advisory,
        details={
            "lint": lint_info,
            "max_nesting": deep,
            "nesting_ok": nesting_ok,
            "test_gap": test_info,
            "checks_run": len(checks),
            "advisory_reason": "ruff not installed — only weak checks ran" if advisory else None,
        },
    )


def _test_gap(task, workdir: str):
    """Do the task's public symbols appear in any test file? Reference check only."""
    if not task.symbols:
        return None, "skipped (task declares no symbols)"
    referenced = find_test_references(task.symbols, workdir)
    missing = sorted(s for s, hits in referenced.items() if not hits)
    if missing:
        return False, f"no test file references: {', '.join(missing)}"
    return True, "every declared symbol is referenced by at least one test file"


def _ruff(abs_files: list[str], workdir: str):
    if shutil.which("ruff") is None:
        return None, "skipped (ruff not installed)"
    proc = subprocess.run(["ruff", "check", *abs_files], cwd=workdir,
                          capture_output=True, text=True)
    return proc.returncode == 0, (proc.stdout.strip() or "clean")


def _max_nesting(abs_files: list[str]) -> int:
    worst = 0
    for path in abs_files:
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError:
            return 99  # unparsable code is maximally bad
        worst = max(worst, _depth(tree, 0))
    return worst


_BLOCKS = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)


def _depth(node: ast.AST, current: int) -> int:
    deepest = current
    for child in ast.iter_child_nodes(node):
        nxt = current + 1 if isinstance(child, _BLOCKS) else current
        deepest = max(deepest, _depth(child, nxt))
    return deepest
