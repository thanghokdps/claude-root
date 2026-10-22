#!/usr/bin/env python3
"""compare-shots.py — screenshots of each screen state against the design frames.

  python3 compare-shots.py <frames-dir> <actual-dir> <out-dir> [--threshold 0.03] [--tolerance 24]

For every <state>.png in frames-dir: the share of pixels whose channels differ by more than --tolerance (0-255)
from actual-dir/<state>.png. Writes <out-dir>/<state>.png = design | actual | diff (changed pixels in red).
A size mismatch is a failure, never rescaled: it means the viewport or deviceScaleFactor is wrong.
Exit 1 when any state fails or is missing; needs Pillow (pip install pillow).
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    print("compare-shots: Pillow is missing — pip install pillow, or compare the images side by side by eye")
    sys.exit(2)


def compare(design_path, actual_path, out_path, tolerance):
    design = Image.open(design_path).convert("RGB")
    actual = Image.open(actual_path).convert("RGB")
    if design.size != actual.size:
        return None, f"size {actual.size[0]}x{actual.size[1]} ≠ design {design.size[0]}x{design.size[1]}"
    diff = ImageChops.difference(design, actual)
    mask = diff.convert("L").point(lambda v: 255 if v > tolerance else 0)
    changed = sum(1 for v in mask.getdata() if v)
    ratio = changed / (design.size[0] * design.size[1])
    overlay = design.copy()
    overlay.paste((230, 30, 30), mask=mask)
    w, h = design.size
    sheet = Image.new("RGB", (w * 3, h), (255, 255, 255))
    for i, img in enumerate((design, actual, overlay)):
        sheet.paste(img, (w * i, 0))
    sheet.save(out_path)
    return ratio, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("frames"); ap.add_argument("actual"); ap.add_argument("out")
    ap.add_argument("--threshold", type=float, default=0.03, help="max share of changed pixels per state")
    ap.add_argument("--tolerance", type=int, default=24, help="per-channel difference ignored as rendering noise")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    states = sorted(f for f in os.listdir(a.frames) if f.lower().endswith(".png"))
    if not states:
        print(f"compare-shots: no PNG frames in {a.frames}")
        return 1
    failed = 0
    print(f"{'STATE':28} {'DIFF':>7}  RESULT  (threshold {a.threshold:.1%})")
    for f in states:
        state, actual = f[:-4], os.path.join(a.actual, f)
        if not os.path.isfile(actual):
            print(f"{state:28} {'—':>7}  FAIL    missing screenshot {actual}")
            failed += 1
            continue
        ratio, why = compare(os.path.join(a.frames, f), actual, os.path.join(a.out, f), a.tolerance)
        if ratio is None:
            print(f"{state:28} {'—':>7}  FAIL    {why}")
            failed += 1
        else:
            ok = ratio <= a.threshold
            failed += not ok
            print(f"{state:28} {ratio:>6.1%}  {'PASS' if ok else 'FAIL'}    {os.path.join(a.out, f)}")
    print(f"{len(states) - failed}/{len(states)} states match")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
