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


def test_scope_covers_agent_plugin():
    assert lint_kit.in_denylist_scope("plugins/thang-agent/skills/agent-tool/SKILL.md")
    assert lint_kit.in_denylist_scope("plugins/thang-agent/skills/agent-architect/references/stock-map.md")
    assert lint_kit.in_denylist_scope("plugins/thang-agent/rules/agent-prompts.md")
    assert lint_kit.in_denylist_scope("plugins/thang-agent/README.md")
    assert not lint_kit.in_denylist_scope("plugins/thang-dev/skills/fix-bug/SKILL.md")


OWNERS = {"fix-bug": "thang-dev", "verify-done": "thang-core", "ci-triage": "thang-ship"}


def test_undeclared_cross_plugin_ref_fails():
    hits = lint_kit.undeclared_refs(["hand regressions to `/fix-bug`."], "thang-ship", {"thang-core"}, OWNERS)
    assert hits == [(1, "fix-bug")], hits


def test_soft_declared_and_own_refs_pass():
    lines = ["hand regressions to `/fix-bug` (if installed).", "Run `/verify-done`.", "see `/ci-triage`",
             "if thang-dev is installed, suggest `/fix-bug`"]
    assert lint_kit.undeclared_refs(lines, "thang-ship", {"thang-core"}, OWNERS) == []


def test_dependency_cycle_detected():
    assert lint_kit.find_cycle({"a": ["b"], "b": ["c"], "c": ["a"]}) == ["a", "b", "c", "a"]
    assert lint_kit.find_cycle({"a": ["b"], "b": [], "c": ["a", "b"]}) is None


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_lint_kit: {len(tests)} passed")
