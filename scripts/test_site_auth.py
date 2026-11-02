#!/usr/bin/env python3
"""Tests for middleware.js (the docs site's Basic Auth). Run: python3 scripts/test_site_auth.py"""
import base64
import json
import os
import subprocess
from pathlib import Path

MIDDLEWARE = Path(__file__).resolve().parent.parent / "middleware.js"

# Calls the middleware once and prints {"status": …, "auth": …}, or {"status": "pass"} when it lets the request through.
PROBE = """
const { default: middleware } = await import(process.argv[1]);
const headers = process.argv[2] ? { authorization: process.argv[2] } : {};
const res = middleware(new Request("https://site.test/", { headers }));
console.log(JSON.stringify(res === undefined ? { status: "pass" }
  : { status: res.status, auth: res.headers.get("www-authenticate") }));
"""


def call(authorization="", password=None):
    env = {k: v for k, v in os.environ.items() if k != "SITE_PASSWORD"}
    if password is not None:
        env["SITE_PASSWORD"] = password
    out = subprocess.run(
        ["node", "--input-type=module", "-e", PROBE, str(MIDDLEWARE), authorization],
        env=env, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def basic(credentials):
    return "Basic " + base64.b64encode(credentials.encode()).decode()


def test_no_password_set_locks_the_site():
    assert call(basic("u:anything"))["status"] == 503


def test_no_credentials_asks_for_them():
    result = call(password="s3cret")
    assert result["status"] == 401
    assert result["auth"].startswith("Basic realm=")


def test_wrong_password_is_refused():
    assert call(basic("u:wrong"), password="s3cret")["status"] == 401


def test_right_password_passes_with_any_user():
    assert call(basic("anyone:s3cret"), password="s3cret")["status"] == "pass"


def test_password_containing_a_colon():
    assert call(basic("u:a:b"), password="a:b")["status"] == "pass"


def test_other_scheme_and_garbage_are_refused():
    assert call("Bearer s3cret", password="s3cret")["status"] == 401
    assert call("Basic !!!not-base64", password="s3cret")["status"] == 401
    assert call(basic("s3cret"), password="s3cret")["status"] == 401


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("site auth: all tests passed")
