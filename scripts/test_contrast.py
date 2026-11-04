#!/usr/bin/env python3
"""Tests for design-direction's contrast.py and its mobile copy. Run: python3 scripts/test_contrast.py"""
import filecmp
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "plan", "skills", "design-direction", "scripts", "contrast.py")
COPY = os.path.join(ROOT, "plugins", "mobile", "skills", "mobile-design", "scripts", "contrast.py")


def run(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_black_on_white_is_21():
    code, out = run("#000", "#ffffff")
    assert code == 0 and "PASS 21.00:1" in out, out


def test_translucent_text_is_blended_first():
    code, out = run("rgba(255,255,255,0.38)", "#1C1C1E")
    assert code == 1 and "FAIL 3.55:1" in out, out
    code, out = run("rgba(255,255,255,0.38)", "#1C1C1E", "--role", "large")
    assert code == 0 and "PASS 3.55:1" in out, out


def test_threshold_uses_the_raw_ratio():
    code, out = run("#777777", "#ffffff")  # 4.48:1
    assert code == 1 and "4.48" in out, out
    code, out = run("#767676", "#ffffff")  # 4.54:1
    assert code == 0, out


def test_hsl_and_eight_digit_hex_match_their_rgb():
    want = run("rgb(255, 0, 0)", "#fff")[1].split()[1]
    assert run("hsl(0, 100%, 50%)", "#fff")[1].split()[1] == want
    assert run("#ff0000ff", "#fff")[1].split()[1] == want
    assert run("hsla(0 100% 50% / 100%)", "#fff")[1].split()[1] == want


def test_translucent_background_is_refused():
    code, out = run("#000", "rgba(255,255,255,0.5)")
    assert code == 2 and "must be opaque" in out, out


def test_unreadable_colour_is_refused():
    code, out = run("tomato", "#fff")
    assert code == 2 and "cannot read colour: tomato" in out, out


def test_pairs_file_reports_each_pair():
    pairs = [{"name": "body", "fg": "#000", "bg": "#fff"},
             {"name": "icon", "fg": "#949494", "bg": "#fff", "role": "ui"},
             {"name": "muted", "fg": "#999", "bg": "#fff"}]
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "pairs.json")
        with open(path, "w") as f:
            json.dump(pairs, f)
        code, out = run("--pairs", path)
    assert code == 1 and "1 of 3 pairs fail" in out and "FAIL" in out and "muted" in out, out


def test_mobile_copy_is_identical():
    assert filecmp.cmp(SCRIPT, COPY, shallow=False), "plugins may not share paths, so the two copies must stay equal"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_contrast: {len(tests)}/{len(tests)} passed")
