"""Self-tests for the harness itself (not the golden tasks)."""

import os
import textwrap

import pytest

from evalkit.cassette import Cassette
from evalkit.judges import StubJudge
from evalkit.report import summarize
from evalkit.runner import evaluate_all, evaluate_task, load_tasks
from evalkit.sandbox import scrubbed_env
from evalkit.solvers import CommandSolver, ReferenceSolver

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS = os.path.join(ROOT, "tasks")


def test_cassette_records_and_replays(tmp_path):
    path = str(tmp_path / "c.json")
    c = Cassette(path)
    calls = {"n": 0}

    def produce():
        calls["n"] += 1
        return {"v": 42}

    assert c.call({"a": 1}, produce) == {"v": 42}
    assert c.call({"a": 1}, produce) == {"v": 42}  # replayed, not re-produced
    assert calls["n"] == 1
    assert c.hits == 1 and c.misses == 1

    # A fresh cassette loaded from disk replays without calling produce.
    c2 = Cassette(path)
    assert c2.call({"a": 1}, produce) == {"v": 42}
    assert calls["n"] == 1


def test_reference_solver_resolves_all_tasks():
    tasks = load_tasks(TASKS)
    assert tasks, "no golden tasks found"
    for t in tasks:
        r = evaluate_task(t, ReferenceSolver())
        assert r.error is None, r.error
        assert r.solved, f"{t.id} should be solved by the reference"
        assert not r.lucky_pass_flag, f"{t.id} unexpectedly flagged lucky-pass"
        assert r.grader("correctness").score == 1.0
        assert r.grader("robustness").score == 1.0


def test_every_golden_task_has_heldout_tests():
    """Without heldout tests a task cannot tell a real solution from a hardcoded one."""
    for t in load_tasks(TASKS):
        assert t.heldout, (
            f"task {t.id} has no heldout tests — it would score 100% for a solver "
            f"that hardcodes the visible cases"
        )


def test_hardcoded_solution_passes_correctness_but_fails_robustness(tmp_path):
    """The reward-hacking case: this is what the whole robustness tier exists for."""
    tasks = {t.id: t for t in load_tasks(TASKS)}
    discount = tasks["discount"]

    # Passes every assertion in tests/ by lookup, implements nothing.
    hardcode = textwrap.dedent("""
        cat > pricing.py <<'EOF'
        def apply_discount(price, pct):
            table = {(100, 10): 90, (50, 50): 25, (100, 0): 100, (80, 25): 60}
            return table[(price, pct)]
        EOF
    """)
    result = evaluate_task(discount, CommandSolver(hardcode))

    assert result.error is None, result.error
    assert result.grader("correctness").passed, "the hack does satisfy the visible tests"
    assert not result.grader("robustness").passed, "heldout tests must reject the hack"
    assert not result.solved, "a hardcoded solution must never be reported as solved"


def test_solver_environment_is_scrubbed_of_secrets(monkeypatch, tmp_path):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-never-leak")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "also-secret")
    env = scrubbed_env(str(tmp_path))
    assert "ANTHROPIC_API_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert env["PYTHONPATH"] == str(tmp_path)

    with pytest.raises(ValueError):
        scrubbed_env(str(tmp_path), {"MY_API_TOKEN": "x"})


def test_lucky_pass_marks_the_task_invalid_not_the_solver(tmp_path):
    # A task whose FAIL_TO_PASS test already passes on the untouched workspace
    # measures nothing. That is a benchmark bug, so it must be excluded from the
    # denominator rather than charged to the solver as a failure.
    d = tmp_path / "trivial"
    (d / "workspace").mkdir(parents=True)
    (d / "reference").mkdir()
    (d / "tests").mkdir()
    (d / "workspace" / "mod.py").write_text("def f():\n    return 1\n")
    (d / "reference" / "mod.py").write_text("def f():\n    return 1\n")
    (d / "tests" / "test_mod.py").write_text(
        "from mod import f\n\n\ndef test():\n    assert f() == 1\n"
    )
    (d / "task.yaml").write_text(
        "id: trivial\nmode: bugfix\nprompt: x\ntarget_files: [mod.py]\n"
        "tests:\n  fail_to_pass: [test_mod.py]\n  pass_to_pass: []\n"
    )
    tasks = load_tasks(str(tmp_path))
    r = evaluate_task(tasks[0], ReferenceSolver())
    assert r.lucky_pass_flag
    assert not r.valid and r.invalid_reason

    s = summarize([r])
    assert s["valid_tasks"] == 0
    assert s["invalid_tasks"] == ["trivial"]
    assert s["attempts"] == 0, "an unmeasurable task must not sit in the denominator"


def test_mode_must_match_the_fixtures(tmp_path):
    d = tmp_path / "mismatch"
    (d / "workspace").mkdir(parents=True)
    (d / "tests").mkdir()
    (d / "workspace" / "mod.py").write_text("x = 1\n")
    (d / "task.yaml").write_text(
        "id: mismatch\nmode: greenfield\nprompt: x\ntests:\n  fail_to_pass: []\n"
    )
    with pytest.raises(ValueError, match="greenfield"):
        load_tasks(str(tmp_path))


def test_repeat_reports_pass_at_k():
    tasks = load_tasks(TASKS)
    results = evaluate_all(tasks, ReferenceSolver(), judge=StubJudge(), repeat=2)
    assert len(results) == len(tasks) * 2
    s = summarize(results)
    assert s["repeats"] == 2
    assert s["attempts"] == len(tasks) * 2
    assert s["pass_at_1"] == 1.0
    assert s["pass_at_2"] == 1.0


def test_stub_judge_does_not_credit_prose_that_echoes_the_rubric():
    """The original bug: a docstring containing the rubric's words scored 1.0
    on code that did the opposite. Comments and docstrings are now stripped
    before matching, so only executable text can satisfy a rubric item."""
    judge = StubJudge()
    rubric = ["Divides the percentage by 100"]

    buggy_but_flattering_docstring = (
        'def apply_discount(price, pct):\n'
        '    """Return price after applying a percentage discount."""\n'
        '    return price - price * pct\n'
    )
    assert judge.score("", buggy_but_flattering_docstring, rubric)["score"] == 0.0

    # And it stays 0.0 even for a correct fix, because "divides" is English prose
    # that never appears in the code. The stub errs toward 0 — the safe direction
    # for a placeholder, and precisely why its scores are advisory and uncounted.
    correct = (
        "def apply_discount(price, pct):\n"
        "    percentage = pct / 100\n"
        "    return price - price * percentage\n"
    )
    assert judge.score("", correct, rubric)["score"] == 0.0

    # A rubric phrased in the code's own vocabulary is the only thing it can score.
    assert judge.score("", correct, ["percentage of 100"])["score"] == 1.0


def test_stub_judge_scores_are_advisory_and_never_counted():
    tasks = load_tasks(TASKS)
    r = evaluate_task(tasks[0], ReferenceSolver(), judge=StubJudge())
    assert r.grader("feature").advisory
    assert summarize([r])["tier_scores"]["feature"] is None


def test_security_grader_flags_dangerous_code(tmp_path):
    from evalkit.graders import grade_security
    from evalkit.models import TaskSpec

    (tmp_path / "bad.py").write_text("import os\nos.system(input())\nx = eval(input())\n")
    task = TaskSpec(id="x", mode="greenfield", prompt="", dir=str(tmp_path),
                    target_files=["bad.py"])
    res = grade_security(task, str(tmp_path))
    assert not res.passed
    assert any(f["rule"] == "eval-call" for f in res.details["findings"])
