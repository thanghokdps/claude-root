"""Data structures shared across the harness."""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_MODES = ("greenfield", "bugfix")


@dataclass
class TaskSpec:
    """One evaluation task loaded from tasks/<id>/task.yaml."""

    id: str
    mode: str  # "greenfield" | "bugfix" — validated against the fixtures at load time
    prompt: str
    dir: str  # absolute path to the task directory
    fail_to_pass: list[str] = field(default_factory=list)
    pass_to_pass: list[str] = field(default_factory=list)
    heldout: list[str] = field(default_factory=list)  # never copied in before the solver runs
    rubric: list[str] = field(default_factory=list)
    target_files: list[str] = field(default_factory=list)  # files scanned by static graders
    symbols: list[str] = field(default_factory=list)  # public names, for the test-gap probe


@dataclass
class GraderResult:
    name: str
    passed: bool
    score: float  # 0.0 .. 1.0
    details: dict = field(default_factory=dict)
    skipped: bool = False
    #: True when the score comes from a heuristic rather than a real measurement.
    #: Advisory scores are shown in the report but excluded from tier averages
    #: and from the solved verdict — a placeholder must never look like evidence.
    advisory: bool = False


@dataclass
class TaskResult:
    task_id: str
    solved: bool  # correctness AND robustness passed
    graders: list[GraderResult] = field(default_factory=list)
    lucky_pass_flag: bool = False  # FAIL_TO_PASS tests passed on the untouched workspace
    #: Set when the *task* is not measurable (bad fixtures), as opposed to the
    #: solver failing. Invalid tasks are excluded from the resolution-rate
    #: denominator: a benchmark authoring bug is not a solver failure.
    invalid_reason: str | None = None
    error: str | None = None
    repeat_index: int = 0

    @property
    def valid(self) -> bool:
        return self.invalid_reason is None

    def grader(self, name: str) -> GraderResult | None:
        return next((g for g in self.graders if g.name == name), None)
