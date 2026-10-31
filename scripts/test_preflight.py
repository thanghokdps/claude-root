#!/usr/bin/env python3
"""Tests for plugins/ai/skills/agent-architect/scripts/preflight.sh. Run: python3 scripts/test_preflight.py"""
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "plugins", "ai", "skills", "agent-architect", "scripts", "preflight.sh")
KEYS = ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY", "AZURE_OPENAI_API_KEY")


def run(d, path=None, **env):
    e = {k: v for k, v in os.environ.items() if k not in KEYS}
    if path is not None:
        e["PATH"] = path
    e.update(env)
    p = subprocess.run(["bash", SCRIPT, d], capture_output=True, text=True, env=e)
    rows = {}
    for line in p.stdout.splitlines():
        for name in ("git repo", "model key", "package manager", "git", "node"):
            if line.startswith(name + " "):
                rows[name] = line
                break
    return p.returncode, rows, p.stdout


def good_dir(with_key=True):
    d = tempfile.mkdtemp(prefix="preflight-")
    subprocess.run(["git", "init", "-q", d], check=True)
    if with_key:
        with open(os.path.join(d, ".env"), "w") as f:
            f.write("ANTHROPIC_API_KEY=sk-secret-value\n")
    return d


def tools_only_path(*names):
    """A PATH holding symlinks to just these tools, so the others read as absent."""
    b = tempfile.mkdtemp(prefix="preflight-bin-")
    for n in names:
        os.symlink(shutil.which(n), os.path.join(b, n))
    return b


def test_pass_path_reports_ok_and_hides_key_value():
    code, rows, out = run(good_dir())
    assert code == 0 and "missing:" in out, out
    assert " ok " in rows["git repo"] and "ANTHROPIC_API_KEY (.env)" in rows["model key"], rows
    assert "sk-secret-value" not in out


def test_missing_model_key_is_named():
    code, rows, out = run(good_dir(with_key=False))
    assert code == 0 and "MISSING" in rows["model key"] and "set ANTHROPIC_API_KEY" in rows["model key"], rows


def test_key_from_environment():
    _, rows, _ = run(good_dir(with_key=False), OPENAI_API_KEY="x")
    assert "OPENAI_API_KEY (env)" in rows["model key"], rows


def test_not_a_git_repo_is_named():
    d = tempfile.mkdtemp(prefix="preflight-norepo-")
    code, rows, _ = run(d)
    assert code == 0 and "MISSING" in rows["git repo"] and "git init" in rows["git repo"], rows


def test_missing_git_and_node_report_install_hints():
    path = tools_only_path("bash", "uname", "awk", "date", "dirname", "basename", "grep", "pwd")
    code, rows, out = run(good_dir(), path=path)
    assert code == 0, out
    assert "MISSING" in rows["git"] and "MISSING" in rows["node"], rows
    assert "MISSING" in rows["package manager"], rows


def test_lockfile_picks_package_manager():
    if not shutil.which("npm"):
        return
    d = good_dir()
    open(os.path.join(d, "package-lock.json"), "w").close()
    _, rows, _ = run(d)
    assert " ok " in rows["package manager"] and "npm" in rows["package manager"], rows


if __name__ == "__main__":
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith("test_")]
    for name, t in tests:
        t()
        print(f"ok {name}")
    print(f"test_preflight: {len(tests)} passed")
