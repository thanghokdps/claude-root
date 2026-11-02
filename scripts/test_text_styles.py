#!/usr/bin/env python3
"""Tests for design-ui's check-text-styles.py. Run: python3 scripts/test_text_styles.py"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "frontend", "skills", "design-ui", "scripts", "check-text-styles.py")

SPEC = {"welcome": [{"selector": "h1", "font-family": "Inter", "font-size": "32px", "font-weight": "600",
                     "line-height": "40px", "letter-spacing": "0px", "color": "#1F2937"}]}
APP = {"h1": {"font-family": "Inter, \"Inter Fallback\", sans-serif", "font-size": "32.2px", "font-weight": "600",
              "line-height": "40px", "letter-spacing": "normal", "color": "rgb(31, 41, 55)"}}


def run(spec, actual):
    with tempfile.TemporaryDirectory() as d:
        frames, shots = os.path.join(d, "frames"), os.path.join(d, "actual")
        os.makedirs(frames)
        os.makedirs(shots)
        with open(os.path.join(frames, "text-styles.json"), "w") as f:
            json.dump(spec, f)
        if actual is not None:
            with open(os.path.join(shots, "welcome.styles.json"), "w") as f:
                json.dump(actual, f)
        r = subprocess.run([sys.executable, SCRIPT, frames, shots], capture_output=True, text=True)
        return r.returncode, r.stdout


def test_matching_style_passes_whatever_the_words():
    code, out = run(SPEC, APP)
    assert code == 0 and "PASS welcome" in out, out


def test_wrong_weight_and_colour_fail():
    app = {"h1": dict(APP["h1"], **{"font-weight": "400", "color": "rgb(0, 0, 0)"})}
    code, out = run(SPEC, app)
    assert code == 1 and "font-weight: design 600, app 400" in out and "color" in out, out


def test_other_font_family_fails():
    code, out = run(SPEC, {"h1": dict(APP["h1"], **{"font-family": "Arial, sans-serif"})})
    assert code == 1 and "font-family" in out, out


def test_missing_element_and_missing_file_fail():
    code, out = run(SPEC, {})
    assert code == 1 and "element: design present, app missing" in out, out
    code, out = run(SPEC, None)
    assert code == 1 and "missing" in out, out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_text_styles: {len(tests)}/{len(tests)} passed")
