#!/usr/bin/env python3
"""Tests for release-site.sh. Run: python3 scripts/test_release_site.py"""
import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "release-site.sh"


def run(env_extra, fake_bin):
    env = {"PATH": f"{fake_bin}:/usr/bin:/bin", **env_extra}
    return subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)


def fake_curl(d):
    """A curl stand-in that records its arguments instead of hitting the network."""
    bin_dir = Path(d) / "bin"
    bin_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(f'#!/bin/sh\necho "$@" > {d}/curl-args\n')
    curl.chmod(0o755)
    return bin_dir


def test_missing_hook_url_blocks_without_calling_curl():
    with tempfile.TemporaryDirectory() as d:
        result = run({}, fake_curl(d))
        assert result.returncode == 2, result
        assert "VERCEL_DEPLOY_HOOK_URL is not set" in result.stderr, result.stderr
        assert not (Path(d) / "curl-args").exists()


def test_hook_url_is_posted():
    with tempfile.TemporaryDirectory() as d:
        url = "https://api.vercel.com/v1/integrations/deploy/prj_x/abc"
        result = run({"VERCEL_DEPLOY_HOOK_URL": url}, fake_curl(d))
        assert result.returncode == 0, result
        assert (Path(d) / "curl-args").read_text().split() == ["-fsS", "-X", "POST", url]


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_release_site: {len(tests)} passed")
