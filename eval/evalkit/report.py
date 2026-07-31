"""Aggregate TaskResults into a JSON blob and a Markdown scorecard.

Two rules shape the numbers here:

  Invalid tasks leave the denominator. A task whose FAIL_TO_PASS already passes
  on the untouched workspace measures nothing, and charging that to the solver
  reports a benchmark authoring bug as a capability failure.

  Advisory scores never enter a tier average. The stub judge and a ruff-less
  quality tier produce numbers, but not evidence — averaging them in would make
  a placeholder indistinguishable from a measurement.
"""

from __future__ import annotations

import json
from dataclasses import asdict


def summarize(results: list) -> dict:
    by_task: dict[str, list] = {}
    for r in results:
        by_task.setdefault(r.task_id, []).append(r)

    repeats = max((len(v) for v in by_task.values()), default=0)
    valid_tasks = {tid: runs for tid, runs in by_task.items() if any(r.valid for r in runs)}
    invalid_tasks = {tid: runs for tid, runs in by_task.items() if tid not in valid_tasks}

    attempts = [r for runs in valid_tasks.values() for r in runs if r.valid]
    solved_attempts = sum(1 for r in attempts if r.solved)

    # pass@k: a task counts as solved if ANY of its k attempts solved it.
    pass_at_k = sum(1 for runs in valid_tasks.values() if any(r.solved for r in runs))
    # pass@1: mean success rate per attempt — the honest single-shot number.
    n_valid = len(valid_tasks)

    def tier_avg(name: str):
        vals = [
            g.score
            for r in attempts
            for g in r.graders
            if g.name == name and not g.skipped and not g.advisory
        ]
        return round(sum(vals) / len(vals), 3) if vals else None

    def tier_note(name: str):
        advisory = [g for r in attempts for g in r.graders if g.name == name and g.advisory]
        if not advisory:
            return None
        reason = advisory[0].details.get("advisory_reason") or advisory[0].details.get("judge")
        return f"advisory only ({reason}) — excluded from the average"

    tiers = ("correctness", "robustness", "feature", "quality", "security")
    no_heldout = sorted(
        tid for tid, runs in valid_tasks.items()
        if any((g := r.grader("robustness")) and g.skipped for r in runs)
    )

    return {
        "total_tasks": len(by_task),
        "valid_tasks": n_valid,
        "invalid_tasks": sorted(invalid_tasks),
        "repeats": repeats,
        "attempts": len(attempts),
        "solved_attempts": solved_attempts,
        # Denominator is attempts on valid tasks only.
        "pass_at_1": round(solved_attempts / len(attempts), 3) if attempts else 0.0,
        f"pass_at_{repeats}": round(pass_at_k / n_valid, 3) if n_valid else 0.0,
        "lucky_pass_flags": sum(1 for r in results if r.lucky_pass_flag),
        "tasks_without_heldout": no_heldout,
        "tier_scores": {name: tier_avg(name) for name in tiers},
        "tier_notes": {name: tier_note(name) for name in tiers if tier_note(name)},
        "tasks": [asdict(r) for r in results],
    }


def to_json(results: list) -> str:
    return json.dumps(summarize(results), indent=2, ensure_ascii=False)


def to_markdown(results: list) -> str:
    s = summarize(results)
    k = s["repeats"]
    lines = [
        "# Eval Report",
        "",
        f"**pass@1:** {s['pass_at_1'] * 100:.1f}%  "
        f"({s['solved_attempts']}/{s['attempts']} attempts on {s['valid_tasks']} valid tasks)",
    ]
    if k > 1:
        lines.append(f"**pass@{k}:** {s[f'pass_at_{k}'] * 100:.1f}%  (task solved on at least one of {k} attempts)")
    if s["invalid_tasks"]:
        lines.append(
            f"**Excluded as invalid:** {', '.join(s['invalid_tasks'])} "
            f"— FAIL_TO_PASS already passed unsolved, so the task measures nothing"
        )
    lines += [
        "",
        "| Task | Run | Solved | Correct | Robust | Feature | Quality | Security |",
        "|------|:---:|:------:|:-------:|:------:|:-------:|:-------:|:--------:|",
    ]
    for r in results:
        def cell(name):
            g = r.grader(name)
            if g is None:
                return "—"
            if g.skipped:
                return "skip"
            return f"{g.score:.2f}{'*' if g.advisory else ''}"

        verdict = "⚠️ invalid" if not r.valid else ("✅" if r.solved else "❌")
        lines.append(
            f"| {r.task_id} | {r.repeat_index + 1} | {verdict} | {cell('correctness')} | "
            f"{cell('robustness')} | {cell('feature')} | {cell('quality')} | {cell('security')} |"
        )

    ts = s["tier_scores"]
    scored = ", ".join(f"{key}={value}" for key, value in ts.items() if value is not None)
    lines += ["", f"**Tier averages (measured only):** {scored or 'none'}"]

    if s["tier_notes"]:
        lines += ["", "`*` = advisory, not counted:"]
        lines += [f"- **{key}** — {value}" for key, value in s["tier_notes"].items()]

    if s["tasks_without_heldout"]:
        lines += [
            "",
            "> ⚠️ No held-out tests for: " + ", ".join(s["tasks_without_heldout"]) + ".",
            "> A hardcoded solution would score 100% on these — the run cannot tell them apart.",
        ]

    errored = [r for r in results if r.error]
    if errored:
        lines += ["", "## Errors"]
        lines += [f"- `{r.task_id}` (run {r.repeat_index + 1}): {r.error}" for r in errored]
    return "\n".join(lines) + "\n"
