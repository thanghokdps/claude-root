#!/usr/bin/env python3
"""Tests for plugins/ai/skills/agent-architect/scripts/setup-env.sh. Run: python3 scripts/test_setup_env.py"""
import os
import stat
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "ai", "skills", "agent-architect", "scripts", "setup-env.sh")

TEMPLATE = """# from https://platform.openai.com/api-keys
OPENAI_API_KEY=
# generate: openssl rand -base64 48
INTERNAL_API_TOKEN=
LANGFUSE_SECRET_KEY=""
DEV_USER_NAME="Dev User"
TRACING_PROVIDER=none
"""


def project(template=TEMPLATE, env=None):
    d = tempfile.mkdtemp(prefix="setup-env-")
    if template is not None:
        with open(os.path.join(d, ".env.example"), "w") as f:
            f.write(template)
    if env is not None:
        with open(os.path.join(d, ".env"), "w") as f:
            f.write(env)
    return d


def run(d):
    r = subprocess.run(["bash", SCRIPT, d], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def read(d):
    with open(os.path.join(d, ".env")) as f:
        return f.read()


def test_creates_env_and_generates_token_without_printing_it():
    d = project()
    out = run(d)
    token = next(l for l in read(d).splitlines() if l.startswith("INTERNAL_API_TOKEN=")).split("=", 1)[1].strip('"')
    assert len(token) >= 32, token
    assert token not in out, out
    assert "INTERNAL_API_TOKEN" not in out, out


def test_generates_the_token_when_the_template_quotes_it_empty():
    d = project(template='INTERNAL_API_TOKEN=""\n')
    assert "none" in run(d), read(d)


def test_lists_only_the_values_still_empty():
    out = run(project())
    assert "OPENAI_API_KEY" in out and "LANGFUSE_SECRET_KEY" in out, out
    assert "DEV_USER_NAME" not in out and "TRACING_PROVIDER" not in out, out


def test_keeps_the_filled_values_and_comments():
    d = project()
    run(d)
    text = read(d)
    assert 'DEV_USER_NAME="Dev User"' in text and "# from https://platform.openai.com/api-keys" in text, text


def test_env_is_private_to_the_owner():
    d = project()
    run(d)
    mode = stat.S_IMODE(os.stat(os.path.join(d, ".env")).st_mode)
    assert mode == 0o600, oct(mode)


def test_never_overwrites_an_existing_env():
    d = project(env="OPENAI_API_KEY=user-key\n")
    out = run(d)
    assert read(d) == "OPENAI_API_KEY=user-key\n"
    assert "left unchanged" in out and "user-key" not in out, out


def test_no_template_creates_nothing():
    d = project(template=None)
    out = run(d)
    assert "nothing created" in out and not os.path.exists(os.path.join(d, ".env")), out


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, t in tests:
        t()
        print(f"ok {name}")
    print(f"test_setup_env: {len(tests)} passed")
