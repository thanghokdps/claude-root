"""Tier 2 — feature / spec adherence via LLM-as-judge, cached with a cassette.

The judge scores the produced code against the task rubric (the checklist of what
the feature *must* do). The call goes through a Cassette so repeated runs replay a
recorded judgment instead of paying for the model again.

Judges live in evalkit/judges.py. The default `StubJudge` is an offline keyword
heuristic — it marks its results **advisory**, which keeps them out of tier
averages and out of the solved verdict. Only a real judge (`--judge anthropic`)
produces a score this tier will let count.
"""

from __future__ import annotations

import os

from ..cassette import Cassette
from ..judges import Judge, StubJudge  # re-exported for backwards compatibility
from ..models import GraderResult

__all__ = ["grade_feature", "Judge", "StubJudge"]


def grade_feature(task, workdir: str, judge: Judge, cassette: Cassette) -> GraderResult:
    if not task.rubric:
        return GraderResult("feature", passed=True, score=1.0, skipped=True,
                            details={"reason": "no rubric"})

    advisory = bool(getattr(judge, "heuristic", False))
    code = _read_targets(task, workdir)
    payload = {"judge": judge.name, "prompt": task.prompt, "rubric": task.rubric, "code": code}

    try:
        result = cassette.call(payload, lambda: judge.score(task.prompt, code, task.rubric))
    except Exception as exc:  # a judge outage must not silently score 1.0
        return GraderResult(
            "feature", passed=False, score=0.0, skipped=True, advisory=True,
            details={"reason": f"judge unavailable: {type(exc).__name__}: {exc}"},
        )

    score = float(result.get("score", 0.0))
    return GraderResult(
        name="feature",
        passed=score >= 0.99,  # every rubric item must be satisfied
        score=score,
        advisory=advisory,
        details={
            "per_item": result.get("per_item"),
            "evidence": result.get("evidence"),
            "notes": result.get("notes"),
            "judge": judge.name,
            "advisory": advisory,
            "cache_hits": cassette.hits,
            "cache_misses": cassette.misses,
        },
    )


def _read_targets(task, workdir: str) -> str:
    chunks = []
    for rel in task.target_files:
        path = os.path.join(workdir, rel)
        if os.path.exists(path):
            chunks.append(f"# {rel}\n" + open(path, encoding="utf-8").read())
    return "\n\n".join(chunks)
