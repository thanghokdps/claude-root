#!/usr/bin/env python3
"""check-ui.py — the quality floor of rendered UI: contrast, spacing scale, target size, type-scale sprawl.

  python3 check-ui.py <state>.ui.json [...] [--scale 0,4,8,12,16,24,32] [--max-font-sizes 6] [--json out.json]

Each input is dump-ui-styles.js evaluated in one state of the running app. Reports:
  contrast    text under 4.5:1, or 3:1 for large text (>=24px, or >=18.66px at weight >=700) — WCAG 1.4.3
  spacing     a padding, margin or gap off --scale (default: any multiple of 4px), once per value
  target      an interactive element under 24x24 CSS px, inline links excepted — WCAG 2.5.8
  font-sizes  more distinct text sizes in one state than --max-font-sizes
Disabled controls are exempt from contrast; text on a background image is listed under "skipped", not judged.
Prints a table and writes the JSON (default: check-ui.json beside the first input). Exit 1 on any finding.
"""
import argparse
import json
import os
import re
import sys

TOL = 0.5  # px; rem-based values land on fractions


def parse_rgba(v):
    v = v.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (1.0,)
    m = re.fullmatch(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)", v)
    if not m:
        return None
    return tuple(float(m.group(i)) for i in (1, 2, 3)) + (float(m.group(4)) if m.group(4) else 1.0,)


def luminance(rgb):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    """WCAG ratio of fg (alpha composited over bg) against bg."""
    a = fg[3]
    fg = tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))
    hi, lo = sorted((luminance(fg), luminance(bg[:3])), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def on_scale(v, scale):
    v = abs(v)
    if scale is None:
        return min(v % 4, 4 - v % 4) <= TOL
    return any(abs(v - s) <= TOL for s in scale)


def check_state(state, elements, scale, max_sizes):
    findings, skipped, off_scale, sizes = [], {}, {}, set()
    for e in elements:
        sel = e["selector"]
        if e.get("text"):
            sizes.add(round(e["fontSize"] * 2) / 2)
            fg, bg = parse_rgba(e["color"]), parse_rgba(e["background"])
            if e.get("disabled"):
                pass
            elif e.get("bgImage"):
                skipped.setdefault("contrast-bg-image", []).append(sel)
            elif fg is None or bg is None:
                skipped.setdefault("contrast-unparsed-colour", []).append(sel)
            else:
                large = e["fontSize"] >= 24 or (e["fontSize"] >= 18.66 and e["fontWeight"] >= 700)
                need = 3.0 if large else 4.5
                ratio = contrast(fg, bg)
                if ratio < need:
                    findings.append({"state": state, "rule": "contrast", "selector": sel, "ratio": round(ratio, 2),
                                     "need": need, "detail": f"{ratio:.2f}:1 < {need}:1 ({e['color']} on {e['background']})"})
        for v in [*e["padding"], *e["margin"], *[g for g in e["gap"] if g is not None]]:
            if not on_scale(v, scale):
                off_scale.setdefault(abs(round(v, 2)), []).append(sel)
        if e.get("interactive") and not e.get("inline"):
            w, h = e["box"]
            if w < 24 or h < 24:
                findings.append({"state": state, "rule": "target", "selector": sel, "box": [w, h],
                                 "detail": f"{w:g}x{h:g} < 24x24"})
    for v, sels in sorted(off_scale.items()):
        findings.append({"state": state, "rule": "spacing", "selector": sels[0], "value": v, "count": len(sels),
                         "selectors": sels[:5], "detail": f"{v:g}px off scale, {len(sels)} uses"})
    if len(sizes) > max_sizes:
        findings.append({"state": state, "rule": "font-sizes", "selector": "-", "count": len(sizes),
                         "sizes": sorted(sizes), "detail": f"{len(sizes)} sizes > {max_sizes}: "
                         + ", ".join(f"{s:g}" for s in sorted(sizes))})
    return findings, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--scale", help="spacing tokens in px, comma-separated (from DESIGN.md)")
    ap.add_argument("--max-font-sizes", type=int, default=6)
    ap.add_argument("--json", help="where to write the JSON report")
    args = ap.parse_args()
    scale = [float(s) for s in args.scale.split(",")] if args.scale else None

    findings, skipped = [], {}
    for path in args.inputs:
        state = os.path.basename(path).split(".")[0]
        with open(path) as f:
            dump = json.load(f)
        found, skip = check_state(state, dump["elements"], scale, args.max_font_sizes)
        findings += found
        for k, sels in skip.items():
            skipped.setdefault(k, []).extend(sels)

    out = args.json or os.path.join(os.path.dirname(os.path.abspath(args.inputs[0])), "check-ui.json")
    with open(out, "w") as f:
        json.dump({"findings": findings, "skipped": skipped}, f, indent=2)

    if findings:
        print("| state | rule | selector | detail |\n|---|---|---|---|")
        for x in findings:
            print(f"| {x['state']} | {x['rule']} | `{x['selector']}` | {x['detail']} |")
    for k, sels in skipped.items():
        print(f"skipped {k}: {len(sels)} ({', '.join(sels[:3])}) — check by eye")
    print(f"{len(findings)} findings in {len(args.inputs)} states; JSON: {out}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
