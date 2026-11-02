"""Orchestrates one evaluation run: load tasks -> solve -> grade -> collect.

The ordering inside `evaluate_task` is load-bearing, not incidental:

  1. copy workspace + visible tests, run FAIL_TO_PASS  -> is the task even valid?
  2. reset, copy workspace only,  run the solver       -> the solver sees no tests
  3. copy visible tests, then heldout tests, grade     -> heldout arrive last

Step 2 is why a solver cannot read the assertions it must satisfy, and step 3 is
why a solver that hardcoded the visible cases still fails. Moving the heldout
copy earlier would quietly destroy the only defence against reward hacking.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import yaml

from .cassette import Cassette
from .graders import (
    grade_correctness,
    grade_feature,
    grade_quality,
    grade_robustness,
    grade_security,
    run_pytest_files,
)
from .judges import StubJudge
from .models import VALID_MODES, TaskResult, TaskSpec
from .sandbox import LocalRunner


def load_tasks(tasks_dir: str) -> list[TaskSpec]:
    tasks = []
    for entry in sorted(os.listdir(tasks_dir)):
        spec_path = os.path.join(tasks_dir, entry, "task.yaml")
        if not os.path.exists(spec_path):
            continue
        raw = yaml.safe_load(open(spec_path, encoding="utf-8"))
        tests = raw.get("tests", {})
        task = TaskSpec(
            id=raw["id"],
            mode=raw.get("mode", "greenfield"),
            prompt=raw["prompt"],
            dir=os.path.join(tasks_dir, entry),
            fail_to_pass=tests.get("fail_to_pass", []),
            pass_to_pass=tests.get("pass_to_pass", []),
            heldout=tests.get("heldout", []),
            rubric=raw.get("rubric", []),
            target_files=raw.get("target_files", []),
            symbols=raw.get("symbols", []),
        )
        _validate(task)
        tasks.append(task)
    return tasks


def _validate(task: TaskSpec) -> None:
    """`mode` describes the starting state — check the fixtures actually match it."""
    if task.mode not in VALID_MODES:
        raise ValueError(f"task {task.id}: mode must be one of {VALID_MODES}, got {task.mode!r}")

    workspace = os.path.join(task.dir, "workspace")
    has_files = any(
        name != ".gitkeep"
        for _root, _dirs, files in os.walk(workspace)
        for name in files
    ) if os.path.isdir(workspace) else False

    if task.mode == "bugfix" and not has_files:
        raise ValueError(
            f"task {task.id}: mode 'bugfix' needs buggy code in workspace/, but it is empty"
        )
    if task.mode == "greenfield" and has_files:
        raise ValueError(
            f"task {task.id}: mode 'greenfield' means starting from nothing, "
            f"but workspace/ contains files"
        )

    for rel in task.heldout:
        if not os.path.exists(os.path.join(task.dir, "heldout", rel)):
            raise ValueError(f"task {task.id}: declared heldout test {rel} does not exist")


def evaluate_task(task: TaskSpec, solver, judge=None, cassette: Cassette | None = None,
                  runner=None, repeat_index: int = 0) -> TaskResult:
    judge = judge or StubJudge()
    cassette = cassette or Cassette(path="", enabled=False)
    runner = runner or LocalRunner()

    workdir = tempfile.mkdtemp(prefix=f"eval-{task.id}-")
    try:
        _copytree(os.path.join(task.dir, "workspace"), workdir)  # starting state (may be empty)

        # Task validity: FAIL_TO_PASS must fail on the untouched workspace.
        # This measures the *task*, not the solver — a task that fails it is
        # unmeasurable, and is excluded from the denominator rather than being
        # counted as a solver failure.
        _copytree(os.path.join(task.dir, "tests"), workdir)
        pre_pass = run_pytest_files(task.fail_to_pass, workdir, runner=runner)
        lucky = bool(task.fail_to_pass) and pre_pass

        # Reset, run the solver against the bare workspace. No tests are present,
        # so the solver cannot read the assertions it is about to be graded on.
        _reset(workdir)
        _copytree(os.path.join(task.dir, "workspace"), workdir)
        solver.solve(task, workdir)

        # Grading fixtures arrive only now.
        _copytree(os.path.join(task.dir, "tests"), workdir)
        _copytree(os.path.join(task.dir, "heldout"), workdir)

        graders = [
            grade_correctness(task, workdir, runner=runner),
            grade_robustness(task, workdir, runner=runner),
            grade_feature(task, workdir, judge, cassette),
            grade_quality(task, workdir),
            grade_security(task, workdir),
        ]
        correctness = next(g for g in graders if g.name == "correctness")
        robustness = next(g for g in graders if g.name == "robustness")

        return TaskResult(
            task_id=task.id,
            # Execution AND generalization. Robustness is `skipped` (passed=True)
            # for tasks with no heldout suite, so those degrade to the old
            # correctness-only signal rather than failing outright.
            solved=correctness.passed and robustness.passed,
            graders=graders,
            lucky_pass_flag=lucky,
            invalid_reason="FAIL_TO_PASS already passed on the untouched workspace" if lucky else None,
            repeat_index=repeat_index,
        )
    except Exception as exc:  # a crashing solver/grader fails the task, not the run
        return TaskResult(
            task_id=task.id, solved=False, error=f"{type(exc).__name__}: {exc}",
            repeat_index=repeat_index,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def evaluate_all(tasks: list[TaskSpec], solver, judge=None, cassette=None,
                 runner=None, repeat: int = 1) -> list[TaskResult]:
    """Run every task `repeat` times. Agents are stochastic; one sample is anecdote."""
    return [
        evaluate_task(t, solver, judge, cassette, runner, repeat_index=i)
        for i in range(repeat)
        for t in tasks
    ]


def _copytree(src: str, dst: str) -> None:
    if not os.path.isdir(src):
        return
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        for name in files:
            if name == ".gitkeep":
                continue
            target_dir = os.path.join(dst, rel) if rel != "." else dst
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(os.path.join(root, name), os.path.join(target_dir, name))


def _reset(workdir: str) -> None:
    for name in os.listdir(workdir):
        path = os.path.join(workdir, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
