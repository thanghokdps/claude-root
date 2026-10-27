#!/usr/bin/env python3
"""check-text-styles.py — the type style of dynamic text against the design, ignoring the words.

  python3 check-text-styles.py <frames-dir> <actual-dir>

Text whose words change on every run (the agent's answers, a generated title, a time-of-day greeting) is masked
out of compare-shots.py; this checks that it still looks right. <frames-dir>/text-styles.json holds the design's
style per state and selector:
  {"<state>": [{"selector": "h1", "font-family": "Inter", "font-size": "32px", "font-weight": "600",
                "line-height": "40px", "letter-spacing": "0px", "color": "#1F2937"}]}
<actual-dir>/<state>.styles.json holds the running app's computed style per selector, written by evaluating
dump-text-styles.js in the page (its selectors argument = the selectors listed for that state).
font-family compares the first family, sizes within 0.5px, colours as RGB. Exit 1 when any value differs or is missing.
"""
import json
import os
import re
import sys

PROPS = ("font-family", "font-size", "font-weight", "line-height", "letter-spacing", "color")


def norm_family(v):
    return v.split(",")[0].strip().strip("'\"").lower()


def norm_color(v):
    v = v.strip().lower()
    m = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", v)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    m = re.fullmatch(r"rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.]+%?))?\s*\)", v)
    if m:
        return tuple(int(m.group(i)) for i in (1, 2, 3))
    return v


def px(v):
    m = re.fullmatch(r"(-?[\d.]+)px", v.strip())
    return float(m.group(1)) if m else None


def same(prop, want, got):
    want, got = str(want), str(got)
    if prop == "font-family":
        return norm_family(want) == norm_family(got)
    if prop == "color":
        return norm_color(want) == norm_color(got)
    if prop == "letter-spacing" and {want.strip(), got.strip()} <= {"normal", "0px", "0"}:
        return True
    a, b = px(want), px(got)
    if a is not None and b is not None:
        return abs(a - b) <= 0.5
    return want.strip().lower() == got.strip().lower()


def check(spec, actual):
    """[(selector, prop, want, got)] for every value that differs or is missing."""
    bad = []
    for item in spec:
        sel = item["selector"]
        got = actual.get(sel)
        if got is None:
            bad.append((sel, "element", "present", "missing"))
            continue
        for prop in PROPS:
            if prop in item and not same(prop, item[prop], got.get(prop, "")):
                bad.append((sel, prop, item[prop], got.get(prop, "missing")))
    return bad


def main():
    if len(sys.argv) != 3:
        print(__doc__.strip().splitlines()[2].strip())
        return 2
    frames, actual_dir = sys.argv[1:]
    with open(os.path.join(frames, "text-styles.json")) as f:
        specs = json.load(f)
    failed = 0
    for state in sorted(specs):
        path = os.path.join(actual_dir, f"{state}.styles.json")
        if not os.path.exists(path):
            print(f"FAIL {state}: {path} missing — run dump-text-styles.js in that state")
            failed += 1
            continue
        with open(path) as f:
            bad = check(specs[state], json.load(f))
        if bad:
            failed += 1
            print(f"FAIL {state}")
            for sel, prop, want, got in bad:
                print(f"     {sel} {prop}: design {want}, app {got}")
        else:
            print(f"PASS {state}: {len(specs[state])} text styles match")
    print(f"{len(specs) - failed}/{len(specs)} states pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
