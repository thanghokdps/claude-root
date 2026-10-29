#!/usr/bin/env python3
"""Tests for scripts/check-upstream.sh. Run: python3 scripts/test_check_upstream.py"""
import datetime
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "check-upstream.sh")


def kit(refs, npm_exit, npm_out="9.9.9"):
    """A copy of the script in a temp kit with its own upstream.json, references and a stub npm."""
    path = tempfile.mkdtemp(prefix="check-upstream-")
    os.makedirs(os.path.join(path, "scripts"))
    shutil.copy(SCRIPT, os.path.join(path, "scripts"))
    upstream = {}
    for ref, (pkg, text) in refs.items():
        upstream.setdefault(pkg, []).append(ref)
        if text is not None:
            with open(os.path.join(path, ref), "w") as f:
                f.write(text)
    with open(os.path.join(path, "scripts", "upstream.json"), "w") as f:
        json.dump(upstream, f)
    bin_dir = os.path.join(path, "bin")
    os.makedirs(bin_dir)
    with open(os.path.join(bin_dir, "npm"), "w") as f:
        f.write(f"#!/bin/sh\n[ \"$1\" = view ] && echo {npm_out}\nexit {npm_exit}\n")
    os.chmod(os.path.join(bin_dir, "npm"), 0o755)
    return path, bin_dir


def run(path, bin_dir, max_age="30"):
    env = {**os.environ, "PATH": bin_dir + os.pathsep + os.environ["PATH"], "MAX_AGE_DAYS": max_age}
    r = subprocess.run(["bash", os.path.join(path, "scripts", "check-upstream.sh")], env=env, capture_output=True, text=True)
    return r.returncode, r.stdout


def dated(days_ago):
    d = datetime.date.today() - datetime.timedelta(days=days_ago)
    return f"Checked against the docs on {d.isoformat()}.\n"


def test_online_fresh_reference_prints_latest_and_no_warning():
    path, bin_dir = kit({"a.md": ("@x/core", dated(2))}, npm_exit=0)
    code, out = run(path, bin_dir)
    assert code == 0
    assert "@x/core" in out and "9.9.9" in out and "re-check" not in out.split("\n\n")[0], out
    assert "0 reference(s) to re-check" in out, out


def test_old_undated_and_missing_references_are_flagged():
    path, bin_dir = kit({"old.md": ("@x/core", dated(40)), "plain.md": ("@x/core", "no date here\n"),
                         "gone.md": ("@x/ui", None)}, npm_exit=0)
    code, out = run(path, bin_dir)
    assert code == 0
    assert "⚠ re-check" in out and "undated" in out and "missing" in out, out
    assert "3 reference(s) to re-check" in out, out


def test_offline_skips_versions_and_still_exits_zero():
    path, bin_dir = kit({"a.md": ("@x/core", dated(1))}, npm_exit=1)
    code, out = run(path, bin_dir)
    assert code == 0
    assert "registry unreachable" in out and "9.9.9" not in out, out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_check_upstream: {len(tests)} passed")
