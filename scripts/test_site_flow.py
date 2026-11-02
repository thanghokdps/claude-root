#!/usr/bin/env python3
"""Tests for the docs site's "Watch it run" walk-through (site/flow.json, built by build-site.py's flow()).
Run: python3 scripts/test_site_flow.py"""
import copy
import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build-site.py")
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)
FLOW = json.loads((ROOT / "site/flow.json").read_text())


def repo_with(flow):
    """A copy of the real flow's cited files and hooks.json files, with flow.json replaced."""
    d = Path(tempfile.mkdtemp())
    for src in [*ROOT.glob("plugins/*/hooks/hooks.json"), *(ROOT / p for p in cited(FLOW))]:
        dest = d / src.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    (d / "site").mkdir(exist_ok=True)
    (d / "site/flow.json").write_text(json.dumps(flow))
    return d


def cited(flow):
    paths = {s["source"] for s in flow["steps"]}
    paths |= {e["source"] for s in flow["steps"] for e in s["lanes"].values() if "source" in e}
    return paths


def raises(flow, needle):
    d = repo_with(flow)
    try:
        build_site.flow(d)
    except ValueError as e:
        assert needle in str(e), e
    else:
        raise AssertionError(f"no error naming {needle}")
    finally:
        shutil.rmtree(d)


def test_real_flow_covers_every_lane_with_real_hooks():
    data = build_site.flow(ROOT)
    assert [lane["id"] for lane in data["lanes"]] == ["tiny", "normal", "high-risk"]
    for step in data["steps"]:
        assert set(step["lanes"]) == {"tiny", "normal", "high-risk"}, step["id"]
        for lane, entry in step["lanes"].items():
            assert ("skip" in entry) != ("text" in entry), (step["id"], lane)
            assert (ROOT / entry["source"]).is_file(), entry["source"]
            for hook in entry.get("hooks", []):
                assert hook["state"] in {"fires", "watching", "records", "blocks", "asks", "idle"}, hook
    gates = {h["name"] for s in data["steps"] for e in s["lanes"].values() for h in e.get("hooks", [])}
    assert {"branch-guard", "ticket-gate", "test-lock", "weakened-check"} <= gates, gates
    assert data["hooks"]["ticket-gate"]["on"] == ["PreToolUse · Bash|mcp__github__create_pull_request"], data["hooks"]


def test_star_entry_fills_omitted_lanes():
    data = build_site.flow(ROOT)
    breakdown = next(s for s in data["steps"] if s["id"] == "breakdown")
    assert "skip" in breakdown["lanes"]["tiny"]
    assert breakdown["lanes"]["normal"] == breakdown["lanes"]["high-risk"] and "text" in breakdown["lanes"]["normal"]


def test_unknown_hook_fails_the_build():
    flow = copy.deepcopy(FLOW)
    flow["steps"][0]["lanes"]["*"]["hooks"].append({"name": "no-such-guard", "state": "blocks", "note": "x"})
    raises(flow, "no-such-guard")


def test_missing_source_fails_the_build():
    flow = copy.deepcopy(FLOW)
    flow["steps"][0]["source"] = "plugins/core/skills/gone/SKILL.md"
    raises(flow, "plugins/core/skills/gone/SKILL.md")


def test_lane_without_an_entry_fails_the_build():
    flow = copy.deepcopy(FLOW)
    flow["steps"][0]["lanes"] = {"tiny": flow["steps"][0]["lanes"]["*"]}
    raises(flow, "lane normal")


def test_page_renders_the_flow_section_from_site_json():
    page = (ROOT / "site/index.html").read_text()
    assert '<section id="flow">' in page and 'href="#flow"' in page
    assert re.search(r"site\.flow\b", page), "the section must render from site.json, not a copy in the page"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
