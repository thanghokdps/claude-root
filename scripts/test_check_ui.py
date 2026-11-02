#!/usr/bin/env python3
"""Tests for design-ui's check-ui.py. Run: python3 scripts/test_check_ui.py"""
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "frontend", "skills", "design-ui", "scripts", "check-ui.py")


def el(selector, **kw):
    base = {"selector": selector, "tag": "p", "text": "Hello", "interactive": False, "inline": False,
            "disabled": False, "color": "rgb(0, 0, 0)", "background": "rgb(255, 255, 255)", "bgImage": False,
            "fontSize": 16, "fontWeight": 400, "padding": [0, 0, 0, 0], "margin": [0, 0, 0, 0],
            "gap": [None, None], "box": [200, 24]}
    base.update(kw)
    return base


def run(elements, *args):
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "home.ui.json")
        with open(path, "w") as f:
            json.dump({"viewport": [1280, 800], "elements": elements}, f)
        out = os.path.join(d, "check-ui.json")
        r = subprocess.run([sys.executable, SCRIPT, path, "--json", out, *args], capture_output=True, text=True)
        with open(out) as f:
            report = json.load(f)
        return r.returncode, r.stdout, report


def rules(report):
    return [x["rule"] for x in report["findings"]]


def test_777_on_white_fails_and_767676_passes():
    code, out, report = run([el("p.grey", color="rgb(119, 119, 119)")])
    assert code == 1 and rules(report) == ["contrast"], out
    assert report["findings"][0]["ratio"] == 4.48 and "4.48" in out, out
    code, out, report = run([el("p.grey", color="rgb(118, 118, 118)")])
    assert code == 0 and report["findings"] == [], out


def test_large_and_bold_text_need_only_3_to_1():
    grey = "rgb(150, 150, 150)"  # 2.96:1 on white
    darker = "rgb(148, 148, 148)"  # 3.03:1
    assert run([el("h2", color=darker, fontSize=24)])[0] == 0
    assert run([el("h3", color=darker, fontSize=18.66, fontWeight=700)])[0] == 0
    assert rules(run([el("h3", color=darker, fontSize=18.66, fontWeight=400)])[2]) == ["contrast"]
    assert rules(run([el("h2", color=grey, fontSize=24)])[2]) == ["contrast"]


def test_translucent_text_is_composited_on_its_background():
    code, out, report = run([el("p", color="rgba(0, 0, 0, 0.5)")])  # ≈ #808080 on white, 3.9:1
    assert code == 1 and rules(report) == ["contrast"], out


def test_disabled_text_and_image_backgrounds_are_skipped():
    code, out, report = run([el("button", color="rgb(200, 200, 200)", disabled=True, box=[40, 40]),
                             el("p.hero", color="rgb(255, 255, 255)", bgImage=True)])
    assert code == 0, out
    assert report["skipped"] == {"contrast-bg-image": ["p.hero"]}, report


def test_spacing_off_the_4px_grid_fails():
    code, out, report = run([el("div.card", text="", padding=[13, 16, 13, 16], gap=[8, 8])])
    assert code == 1 and rules(report) == ["spacing"] and report["findings"][0]["value"] == 13, out


def test_spacing_scale_from_design_md():
    code, out, report = run([el("div.card", text="", padding=[12, 16, 12, 16])], "--scale", "0,4,8,16,24")
    assert code == 1 and report["findings"][0]["value"] == 12, out
    code, out, report = run([el("div.card", text="", padding=[8, 16, 8, 16], margin=[-4, 0, 0, 0])],
                            "--scale", "0,4,8,16,24")
    assert code == 0, out


def test_small_targets_fail_but_inline_links_pass():
    small = el("button.icon", tag="button", text="", interactive=True, box=[20, 20])
    inline = el("p a", tag="a", interactive=True, inline=True, box=[40, 18])
    exact = el("button.ok", tag="button", interactive=True, box=[24, 24])
    code, out, report = run([small, inline, exact])
    assert code == 1 and rules(report) == ["target"] and report["findings"][0]["selector"] == "button.icon", out


def test_too_many_font_sizes_fail():
    texts = [el(f"p.s{n}", fontSize=n) for n in (12, 14, 16, 20, 24, 32, 40)]
    code, out, report = run(texts)
    assert code == 1 and rules(report) == ["font-sizes"] and report["findings"][0]["count"] == 7, out
    assert run(texts, "--max-font-sizes", "7")[0] == 0


def test_table_names_every_finding():
    code, out, _ = run([el("p.grey", color="rgb(119, 119, 119)"),
                        el("button.icon", tag="button", text="", interactive=True, box=[20, 20])])
    assert "| contrast |" in out and "| target |" in out and "home" in out, out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_check_ui: {len(tests)}/{len(tests)} passed")
