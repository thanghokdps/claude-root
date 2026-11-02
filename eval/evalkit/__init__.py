"""evalkit — a small harness for evaluating code produced by an AI agent.

Four grading tiers (see graders/):
  1. correctness — execution-based (pytest, FAIL_TO_PASS + PASS_TO_PASS) + anti-lucky-pass
  2. feature     — LLM-as-judge against a rubric, cached via a cassette
  3. quality     — lint + complexity (static)
  4. security    — pattern-based SAST (static)
"""

from .models import TaskSpec, GraderResult, TaskResult

__all__ = ["TaskSpec", "GraderResult", "TaskResult"]
