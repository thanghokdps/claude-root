#!/usr/bin/env python3
"""Tests for skill-map.py. Run: python3 scripts/test_skill_map.py"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def skill_map(*args):
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "skill-map.py"), *args],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_ai_map_keeps_the_land_view():
    model = skill_map("--plugin", "ai")
    views = [v["id"] for v in model["views"]]
    assert "ai-assistant" in views and "land" in views, views
    assert "p-ship" in model["views"][0]["nodeIds"]


def test_every_pack_map_includes_ship_through_dev():
    model = skill_map("--plugin", "frontend")
    assert any(n["id"] == "p-ship" for n in model["nodes"])
    assert not any(n["id"] == "p-lead" for n in model["nodes"])
    assert [v["id"] for v in model["views"] if v["id"] in ("ai-assistant", "land")] == []


def test_model_is_drawn_as_a_map():
    # the renderer draws the drill-down map only for kind "map"; without it the page renders blank
    assert skill_map()["kind"] == "map"
    assert skill_map("--plugin", "ai")["kind"] == "map"


def test_into_refreshes_the_page_title_with_the_data():
    with tempfile.TemporaryDirectory() as d:
        page = Path(d) / "map.html"
        page.write_text('<title>agent — skill map</title><script id="visual-data" type="application/json">{}</script>',
                        encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "skill-map.py"), "--plugin", "ai", "--into", str(page)],
                       check=True)
        html = page.read_text(encoding="utf-8")
        assert "<title>ai — skill map</title>" in html, html[:200]
        assert '"kind": "map"' in html


def test_readme_map_names_only_real_skills_and_hooks():
    # the SVG is hand-drawn, so nothing else notices a renamed or removed skill
    svg = (ROOT / "docs" / "skill-map.svg").read_text(encoding="utf-8")
    words = " ".join(re.findall(r"<text[^>]*>([^<]+)</text>", svg)).split()
    named = {w[1:] for w in words if re.fullmatch(r"/[a-z][a-z-]*", w)}
    skills = {p.parent.name for p in ROOT.glob("plugins/*/skills/*/SKILL.md")}
    assert named and named <= skills, named - skills
    chips = set(re.findall(r'class="box rose"[^>]*/>\s*<text[^>]*>([^<]+)<', svg))
    hooks = {p.stem for p in ROOT.glob("plugins/*/hooks/*.sh")}
    assert chips and chips <= hooks, chips - hooks


def test_readme_map_animates_without_a_script():
    # GitHub and GitLab show it through <img>, where scripts never run
    svg = (ROOT / "docs" / "skill-map.svg").read_text(encoding="utf-8")
    assert "<script" not in svg and "@keyframes" in svg and "<animateMotion" in svg


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
