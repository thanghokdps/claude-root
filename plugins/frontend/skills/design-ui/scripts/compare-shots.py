#!/usr/bin/env python3
"""compare-shots.py — screenshots of each screen state against the design frames.

  python3 compare-shots.py <frames-dir> <actual-dir> <out-dir> [--threshold 0.03] [--tolerance 24] [--masks masks.json]

For every <state>.png in frames-dir: the share of pixels whose channels differ by more than --tolerance (0-255)
from actual-dir/<state>.png. Writes <out-dir>/<state>.png = design | actual | diff (changed pixels in red).
--masks (default <frames-dir>/masks.json when present) maps a state to [x, y, w, h] boxes in frame pixels whose
content is expected to differ, such as the agent's answer text: they are left out of the share and drawn grey.
A size mismatch is a failure, never rescaled: it means the viewport or deviceScaleFactor is wrong.
Exit 1 when any state fails or is missing; needs Pillow (pip install pillow).
"""
import argparse
import json
import os
import sys

try:
    from PIL import Image, ImageChops
except ImportError:
    print("compare-shots: Pillow is missing — pip install pillow, or compare the images side by side by eye")
    sys.exit(2)


def compare(design_path, actual_path, out_path, tolerance, boxes=()):
    design = Image.open(design_path).convert("RGB")
    actual = Image.open(actual_path).convert("RGB")
    if design.size != actual.size:
        return None, f"size {actual.size[0]}x{actual.size[1]} ≠ design {design.size[0]}x{design.size[1]}"
    diff = ImageChops.difference(design, actual)
    mask = diff.convert("L").point(lambda v: 255 if v > tolerance else 0)
    ignored = Image.new("L", design.size, 0)
    for x, y, bw, bh in boxes:
        ignored.paste(255, (x, y, x + bw, y + bh))
    mask = ImageChops.subtract(mask, ignored)
    changed = sum(1 for v in mask.getdata() if v)
    counted = design.size[0] * design.size[1] - sum(1 for v in ignored.getdata() if v)
    ratio = changed / counted if counted else 0.0
    overlay = design.copy()
    overlay.paste((150, 150, 150), mask=ignored)
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
    ap.add_argument("--masks", help="JSON {state: [[x, y, w, h], ...]} of boxes left out (default <frames>/masks.json)")
    a = ap.parse_args()
    masks_path = a.masks or os.path.join(a.frames, "masks.json")
    masks = json.load(open(masks_path)) if os.path.isfile(masks_path) else {}
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
        ratio, why = compare(os.path.join(a.frames, f), actual, os.path.join(a.out, f), a.tolerance, masks.get(state, ()))
        if ratio is None:
            print(f"{state:28} {'—':>7}  FAIL    {why}")
            failed += 1
        else:
            ok = ratio <= a.threshold
            failed += not ok
            note = f"  ({len(masks[state])} masked)" if masks.get(state) else ""
            print(f"{state:28} {ratio:>6.1%}  {'PASS' if ok else 'FAIL'}    {os.path.join(a.out, f)}{note}")
    print(f"{len(states) - failed}/{len(states)} states match")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
