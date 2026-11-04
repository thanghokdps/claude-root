#!/usr/bin/env python3
"""contrast.py — WCAG contrast of colour pairs, measured instead of judged by eye.

  python3 contrast.py <foreground> <background> [--role text|large|ui]
  python3 contrast.py --pairs pairs.json

Colours: #rgb, #rrggbb, #rrggbbaa, rgb(), rgba(), hsl(), hsla(). A translucent foreground is blended over the
background first, so the ratio is the one people see; the background must be opaque.
pairs.json is a list of {"name": "...", "fg": "...", "bg": "...", "role": "text"}; role defaults to text.
Thresholds: text 4.5:1, large text 3:1, UI (icons, control boundaries) 3:1 — WCAG 1.4.3 and 1.4.11.
Exit 0 when every pair passes, 1 on a failing pair, 2 on input it cannot read.
"""
import argparse
import colorsys
import json
import re
import sys

NEED = {"text": 4.5, "large": 3.0, "ui": 3.0}
NUM = r"(-?[\d.]+)"
SEP = r"[,\s]+"
ALPHA = rf"(?:[,\s/]+{NUM}(%?))?"


def parse_hex(v):
    h = v[1:]
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
        return None
    rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    return (*rgb, int(h[6:8], 16) / 255 if len(h) == 8 else 1.0)


def alpha_of(raw, pct):
    if raw is None:
        return 1.0
    return float(raw) / 100 if pct else float(raw)


def parse_colour(value):
    """(r, g, b, a) with r, g, b in 0-255 and a in 0-1, or None."""
    v = value.strip().lower()
    if v.startswith("#"):
        return parse_hex(v)
    m = re.fullmatch(rf"rgba?\(\s*{NUM}{SEP}{NUM}{SEP}{NUM}{ALPHA}\s*\)", v)
    if m:
        return (float(m[1]), float(m[2]), float(m[3]), alpha_of(m[4], m[5]))
    m = re.fullmatch(rf"hsla?\(\s*{NUM}(?:deg)?{SEP}{NUM}%{SEP}{NUM}%{ALPHA}\s*\)", v)
    if m:
        r, g, b = colorsys.hls_to_rgb(float(m[1]) % 360 / 360, float(m[3]) / 100, float(m[2]) / 100)
        return (r * 255, g * 255, b * 255, alpha_of(m[4], m[5]))
    return None


def luminance(rgb):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blend(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def ratio(fg, bg):
    hi, lo = sorted((luminance(blend(fg, bg)), luminance(bg[:3])), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def measure(pair):
    """One result dict, or raises ValueError with what could not be read."""
    fg, bg = parse_colour(pair["fg"]), parse_colour(pair["bg"])
    role = pair.get("role", "text")
    if fg is None or bg is None:
        raise ValueError(f"cannot read colour: {pair['fg'] if fg is None else pair['bg']}")
    if bg[3] < 1:
        raise ValueError(f"background must be opaque: {pair['bg']}")
    if role not in NEED:
        raise ValueError(f"unknown role: {role}")
    value = ratio(fg, bg)
    # The raw ratio decides: WCAG does not round, so 4.496:1 fails even though it prints as 4.50:1.
    return {"name": pair.get("name", f"{pair['fg']} on {pair['bg']}"), "ratio": round(value, 2), "role": role,
            "need": NEED[role], "pass": value >= NEED[role]}


def load_pairs(args):
    if args.pairs:
        with open(args.pairs, encoding="utf-8") as f:
            return json.load(f)
    return [{"fg": args.fg, "bg": args.bg, "role": args.role}]


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("fg", nargs="?")
    ap.add_argument("bg", nargs="?")
    ap.add_argument("--role", default="text", choices=sorted(NEED))
    ap.add_argument("--pairs", help="JSON list of pairs")
    args = ap.parse_args()
    if not args.pairs and not (args.fg and args.bg):
        ap.error("give <foreground> <background>, or --pairs")
    try:
        results = [measure(p) for p in load_pairs(args)]
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"contrast.py: {e}", file=sys.stderr)
        return 2
    for r in results:
        print(f"{'PASS' if r['pass'] else 'FAIL'} {r['ratio']:.2f}:1 (needs {r['need']}:1, {r['role']})  {r['name']}")
    failed = sum(not r["pass"] for r in results)
    print(f"{failed} of {len(results)} pairs fail")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
