#!/usr/bin/env python3
"""Tests for skill-map.py. Run: python3 scripts/test_skill_map.py"""
import json
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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
