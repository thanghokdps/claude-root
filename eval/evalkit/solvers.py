"""Solvers = the thing under test. A solver receives a task + a working directory
and must leave the produced/edited code in that directory.

- ReferenceSolver: copies the task's reference/ solution. Used to sanity-check the
  harness and establish the upper bound (should score 100%).
- CommandSolver: shells out to an external command (plug your real agent here).
  The command gets TASK_PROMPT and WORK_DIR in its environment and writes files
  into WORK_DIR.

A solver command is arbitrary code chosen by whoever is being evaluated, so it
runs through the same sandbox runner as the graders and gets a scrubbed
environment — never the operator's `os.environ`, which holds their API keys.
"""

from __future__ import annotations

import os
import shutil

from .models import TaskSpec
from .sandbox import LocalRunner


class ReferenceSolver:
    name = "reference"

    def solve(self, task: TaskSpec, workdir: str) -> None:
        ref = os.path.join(task.dir, "reference")
        if not os.path.isdir(ref):
            raise FileNotFoundError(f"task {task.id} has no reference/ directory")
        _overlay(ref, workdir)


class CommandSolver:
    def __init__(self, command: str, timeout: int = 300, runner=None):
        self.name = "command"
        self.command = command
        self.timeout = timeout
        self.runner = runner or LocalRunner()

    def solve(self, task: TaskSpec, workdir: str) -> None:
        # TASK_PROMPT/WORK_DIR are the only additions; everything else comes from
        # the sandbox allowlist. Passing os.environ here would hand the agent
        # under test every credential on the machine.
        proc = self.runner.run(
            self.command,
            workdir=workdir,
            timeout=self.timeout,
            env_extra={"TASK_PROMPT": task.prompt, "WORK_DIR": workdir},
            shell=True,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip()[-500:]
            raise RuntimeError(f"solver exited {proc.returncode}: {tail}")


def _overlay(src: str, dst: str) -> None:
    """Copy every file under src on top of dst, preserving subpaths."""
    for root, _dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        for name in files:
            target_dir = os.path.join(dst, rel) if rel != "." else dst
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy2(os.path.join(root, name), os.path.join(target_dir, name))
