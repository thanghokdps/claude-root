#!/usr/bin/env python3
"""Tests for skill-map.py. Run: python3 scripts/test_skill_map.py"""
import json
import subprocess
import sys
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
    ship = next(n for n in model["nodes"] if n["id"] == "p-ship")
    assert "separately" in ship["when"], ship["when"]
    assert "p-ship" in model["views"][0]["nodeIds"]


def test_other_pack_maps_stay_their_closure():
    model = skill_map("--plugin", "frontend")
    assert not any(n["id"] == "p-ship" for n in model["nodes"])
    assert [v["id"] for v in model["views"] if v["id"] in ("ai-assistant", "land")] == []


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
