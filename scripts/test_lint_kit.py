#!/usr/bin/env python3
"""Tests for lint-kit.py's denylist and plugin dependency checks. Run: python3 scripts/test_lint_kit.py"""
import importlib.util
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("lint_kit", os.path.join(HERE, "lint-kit.py"))
lint_kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_kit)


def test_flags_company_and_internal_names():
    for text in ["see granbull docs", "gitlab.asoft-python.com/x", "the flash-agent repo",
                 "space-agent plugin", "on-behalf tools", "space-v2 frontend", "Granbull"]:
        assert lint_kit.denylist_hits(text), text


def test_allows_generic_text():
    for text in ["createMutationTool with a pending action", "flash of unstyled content",
                 "an outer space metaphor", "GitHub and GitLab both work"]:
        assert not lint_kit.denylist_hits(text), text


def test_inline_python_must_run_isolated():
    for text in ["HOOK_INPUT=x python3 - <<'PY'", "  python3 - \"$F\"", "python3 -c 'print(1)'", "python -"]:
        assert lint_kit.unisolated_python(text) == [1], text
    for text in ["python3 -I - <<'PY'", "python3 -I -c 'x'", "python3 scripts/gen.py", "command -v python3 >/dev/null",
                 "r\"(?:python3?|node)\\s+-[ce]\"", "cat jq python python3 node ruby",
                 "# a comment about python -c \"git push\""]:
        assert lint_kit.unisolated_python(text) == [], text


def test_scope_covers_agent_plugin():
    assert lint_kit.in_denylist_scope("plugins/agent/skills/agent-tool/SKILL.md")
    assert lint_kit.in_denylist_scope("plugins/agent/skills/agent-architect/references/stock-map.md")
    assert lint_kit.in_denylist_scope("plugins/agent/rules/agent-prompts.md")
    assert lint_kit.in_denylist_scope("plugins/agent/README.md")
    assert not lint_kit.in_denylist_scope("plugins/dev/skills/fix-bug/SKILL.md")


OWNERS = {"fix-bug": "dev", "verify-done": "core", "ci-triage": "ship"}


def test_undeclared_cross_plugin_ref_fails():
    hits = lint_kit.undeclared_refs(["hand regressions to `/fix-bug`."], "ship", {"core"}, OWNERS)
    assert hits == [(1, "fix-bug")], hits


def test_soft_declared_and_own_refs_pass():
    lines = ["hand regressions to `/fix-bug` (if installed).", "Run `/verify-done`.", "see `/ci-triage`",
             "if dev is installed, suggest `/fix-bug`"]
    assert lint_kit.undeclared_refs(lines, "ship", {"core"}, OWNERS) == []


def test_dependency_cycle_detected():
    assert lint_kit.find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]
    assert lint_kit.find_cycle({"a": ["b"], "b": [], "c": ["a", "b"]}) is None



def test_unknown_skill_field_is_flagged():
    assert lint_kit.unknown_fields({"name": "x", "description": "d", "colour": "red"}) == ["colour"]
    assert lint_kit.unknown_fields({"name": "x", "context": "fork", "agent": "Explore", "paths": "*.ts"}) == []


def test_listing_text_over_cap_is_flagged():
    assert lint_kit.listing_chars({"description": "a" * 1000, "when_to_use": "b" * 600}) == 1600
    assert lint_kit.listing_chars({"description": "a" * 10}) == 10


def test_init_sh_missing_copy_source_is_flagged():
    script = 'cp "$HARNESS_DIR/rules/stacks/nope.md" x\ncp "$HARNESS_DIR/rules/stacks/python.md" y\nfor r in "$HARNESS_DIR"/rules/*.md; do :; done'
    assert lint_kit.missing_init_sources(script, "plugins/core") == ["rules/stacks/nope.md"]


def test_eval_case_missing_dependency_is_flagged():
    case = "/k/plugins/agent/evals/tool-add"
    assert lint_kit.missing_eval_plugins(None, case, {"agent", "progress"}) == ["agent", "progress"]
    assert lint_kit.missing_eval_plugins(["../..", "../../../progress"], case, {"agent", "progress"}) == []


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_lint_kit: {len(tests)} passed")
