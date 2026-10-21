#!/usr/bin/env python3
"""Tests for lint-kit.py's public-repo denylist. Run: python3 scripts/test_lint_kit.py"""
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


def test_scope_covers_agent_skills_and_rules():
    assert lint_kit.in_denylist_scope("skills/agent-tool/SKILL.md")
    assert lint_kit.in_denylist_scope("skills/agent-architect/references/stock-map.md")
    assert lint_kit.in_denylist_scope("rules/stacks/agent-prompts.md")
    assert lint_kit.in_denylist_scope("rules/stacks/agui-transport.md")
    assert not lint_kit.in_denylist_scope("skills/fix-bug/SKILL.md")


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_lint_kit: {len(tests)} passed")
