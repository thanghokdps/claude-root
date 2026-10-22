#!/usr/bin/env python3
"""Tests for design-ui's compare-shots.py. Run: python3 scripts/test_compare_shots.py (skips without Pillow)."""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "dev", "skills", "design-ui", "scripts", "compare-shots.py")

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("test_compare_shots: skipped (no Pillow)")
    sys.exit(0)


def frame(path, size=(200, 120), block=None, noise=0):
    img = Image.new("RGB", size, (245, 245, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 180, 50], fill=(60, 90, 220))  # a "bubble"
    if block:
        d.rectangle(block, fill=(230, 40, 40))
    for i in range(noise):  # scattered 1-px differences, like anti-aliasing
        img.putpixel(((i * 37) % size[0], (i * 53) % size[1]), (0, 0, 0))
    img.save(path)


def run(design, actual, out, *extra):
    r = subprocess.run([sys.executable, SCRIPT, design, actual, out, *extra], capture_output=True, text=True)
    return r.returncode, r.stdout


def setup(case, **actual_kwargs):
    base = tempfile.mkdtemp(prefix=f"shots-{case}-")
    d, a, o = (os.path.join(base, x) for x in ("frames", "actual", "diff"))
    os.makedirs(d); os.makedirs(a)
    frame(os.path.join(d, "welcome.png"))
    if actual_kwargs is not None and actual_kwargs.get("skip") is not True:
        frame(os.path.join(a, "welcome.png"), **{k: v for k, v in actual_kwargs.items() if k != "skip"})
    return d, a, o


def test_identical_passes_and_writes_side_by_side():
    d, a, o = setup("same")
    code, out = run(d, a, o)
    assert code == 0 and "welcome" in out and "PASS" in out, out
    assert os.path.isfile(os.path.join(o, "welcome.png"))


def test_antialias_noise_stays_under_threshold():
    code, out = run(*setup("noise", noise=200))  # 200 of 24000 px ≈ 0.8%
    assert code == 0 and "PASS" in out, out


def test_wrong_block_fails():
    code, out = run(*setup("block", block=[20, 70, 120, 110]))  # ≈ 17% of the frame
    assert code == 1 and "FAIL" in out, out


def test_size_mismatch_is_reported_not_scaled_silently():
    code, out = run(*setup("size", size=(400, 240)))
    assert code == 1 and "size" in out.lower(), out


def test_missing_screenshot_is_a_failure():
    code, out = run(*setup("missing", skip=True))
    assert code == 1 and "missing" in out.lower(), out


def test_threshold_flag():
    code, out = run(*setup("thr", noise=200), "--threshold", "0.001")
    assert code == 1 and "FAIL" in out, out


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_compare_shots: {len(tests)} passed")
