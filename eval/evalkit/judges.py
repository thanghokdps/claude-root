"""Judges for the feature tier.

`AnthropicJudge` is the real one: it scores the produced code against the task
rubric using the Messages API with a JSON schema, so the response is guaranteed
parseable rather than prompted-and-hoped-for.

`StubJudge` is an offline keyword heuristic. It exists so the suite runs with no
API key, and it is deliberately crippled compared to the real judge:

  - it matches on code with comments and docstrings stripped, because otherwise
    a docstring echoing the rubric wording scores 1.0 on unfixed code
  - it requires *every* keyword in a rubric line, not any one of them
  - its results never count toward tier averages or the solved verdict

Treat a stub score as a smoke-test signal, never as evidence a feature is right.
"""

from __future__ import annotations

import ast
import json
import os
import re
from typing import Protocol

#: Default judge model. Override with EVALKIT_JUDGE_MODEL.
DEFAULT_JUDGE_MODEL = "claude-opus-5"

_SCHEMA = {
    "type": "object",
    "properties": {
        "per_item": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "satisfied": {"type": "boolean"},
                    "evidence": {
                        "type": "string",
                        "description": "Quote the exact line of code that decides it, or say what is missing.",
                    },
                },
                "required": ["criterion", "satisfied", "evidence"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["per_item", "notes"],
    "additionalProperties": False,
}

_SYSTEM = """\
You grade whether code satisfies each item of a rubric. You are strict.

Rules:
- Judge only what the code actually does when executed. Comments, docstrings, \
names, and TODOs are not evidence that a behaviour exists.
- A hardcoded lookup table keyed on specific inputs does NOT satisfy a rubric \
item that asks for a computed behaviour. Mark it unsatisfied and say so.
- Quote the deciding line in `evidence`, or state precisely what is absent.
- Return one entry per rubric item, in the order given.\
"""


class Judge(Protocol):
    name: str

    def score(self, prompt: str, code: str, rubric: list[str]) -> dict:
        """Return {"per_item": [bool,...], "score": float, "notes": str}."""
        ...


class AnthropicJudge:
    """LLM-as-judge over the Messages API, constrained to a JSON schema."""

    def __init__(self, model: str | None = None, max_tokens: int = 8000):
        self.model = model or os.environ.get("EVALKIT_JUDGE_MODEL", DEFAULT_JUDGE_MODEL)
        self.name = f"anthropic:{self.model}"
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - depends on env
                raise RuntimeError(
                    "AnthropicJudge needs the SDK: pip install anthropic"
                ) from exc
            self._client = anthropic.Anthropic()
        return self._client

    def score(self, prompt: str, code: str, rubric: list[str]) -> dict:
        import anthropic

        numbered = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(rubric))
        user = (
            f"<task>\n{prompt.strip()}\n</task>\n\n"
            f"<rubric>\n{numbered}\n</rubric>\n\n"
            f"<code>\n{code or '(no code was produced)'}\n</code>"
        )

        try:
            response = self._get_client().messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=_SYSTEM,
                # No temperature/top_p: removed on this model family, and a judge
                # wants the model's own calibration anyway.
                output_config={
                    "effort": "medium",
                    "format": {"type": "json_schema", "schema": _SCHEMA},
                },
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.NotFoundError as exc:
            raise RuntimeError(f"unknown judge model {self.model!r}: {exc}") from exc
        except anthropic.RateLimitError as exc:
            raise RuntimeError(f"judge rate limited: {exc}") from exc
        except anthropic.APIStatusError as exc:
            raise RuntimeError(f"judge API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise RuntimeError(f"could not reach the judge API: {exc}") from exc

        if response.stop_reason == "refusal":
            raise RuntimeError("judge refused to grade this sample")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("judge response truncated — raise max_tokens")

        text = next((b.text for b in response.content if b.type == "text"), "")
        parsed = json.loads(text)
        items = parsed.get("per_item", [])
        flags = [bool(i.get("satisfied")) for i in items]
        return {
            "per_item": flags,
            "score": (sum(flags) / len(flags)) if flags else 0.0,
            "notes": parsed.get("notes", ""),
            "evidence": [i.get("evidence", "") for i in items],
            "judge_model": self.model,
        }


class StubJudge:
    """Offline keyword heuristic. Deterministic, no API key, and not trustworthy."""

    name = "stub"
    #: Read by the report so stub scores never inflate a tier average.
    heuristic = True

    def score(self, prompt: str, code: str, rubric: list[str]) -> dict:
        # Strip comments and docstrings first: matching them lets a solver satisfy
        # a rubric by restating it in prose above code that does the opposite.
        haystack = _strip_prose(code).lower()
        per_item = []
        for item in rubric:
            keywords = _keywords(item)
            # every keyword, not any — `any` matched on a single common word
            per_item.append(bool(keywords) and all(k in haystack for k in keywords))
        score = sum(per_item) / len(per_item) if per_item else 1.0
        return {
            "per_item": per_item,
            "score": score,
            "notes": "stub keyword heuristic — not a judgment of behaviour",
        }


def _strip_prose(code: str) -> str:
    """Remove comments and docstrings so only executable text remains."""
    without_comments = re.sub(r"#[^\n]*", "", code)
    try:
        tree = ast.parse(without_comments)
    except SyntaxError:
        return without_comments
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            doc = ast.get_docstring(node, clean=False)
            if doc:
                without_comments = without_comments.replace(doc, "")
    return without_comments


_STOP = {"the", "a", "an", "is", "are", "and", "or", "of", "to", "for", "with",
         "that", "must", "should", "it", "its", "handles", "handle", "exists",
         "returns", "return", "named", "function"}


def _keywords(rubric_item: str) -> list[str]:
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]+", rubric_item.lower())
    return [w for w in words if w not in _STOP and len(w) > 2]


def build_judge(name: str) -> Judge:
    if name == "stub":
        return StubJudge()
    if name == "anthropic":
        return AnthropicJudge()
    raise SystemExit(f"unknown judge: {name} (expected 'stub' or 'anthropic')")
