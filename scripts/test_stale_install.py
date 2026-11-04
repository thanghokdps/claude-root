#!/usr/bin/env python3
"""Tests for plugins/core/hooks/stale-install.sh. Run: python3 scripts/test_stale_install.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "stale-install.sh")


def run(home):
    env = {**os.environ, "HOME": home}
    r = subprocess.run(["bash", HOOK], input="{}", capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    assert r.stderr == "", r.stderr
    return r.stdout


def clone(home):
    """A marketplace clone with one commit; returns its path and HEAD."""
    path = os.path.join(home, "clone")
    os.makedirs(path)
    git = ["git", "-C", path, "-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    return path, head


def write_json(home, name, data):
    path = os.path.join(home, ".claude", "plugins", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def installed(home, *entries):
    write_json(home, "installed_plugins.json", {"version": 2, "plugins": {"core@harness": list(entries)}})


def marketplace(home, location, source="github"):
    write_json(home, "known_marketplaces.json", {"harness": {"source": {"source": source}, "installLocation": location}})


def entry(sha, scope="user", updated="2026-11-03T00:00:00Z"):
    return {"scope": scope, "lastUpdated": updated, "gitCommitSha": sha}


def setup():
    home = tempfile.mkdtemp(prefix="stale-install-")
    return (home, *clone(home))


def test_stale_prints_one_additional_context_line():
    home, path, _ = setup()
    marketplace(home, path)
    installed(home, entry("a" * 40))
    out = json.loads(run(home))["hookSpecificOutput"]
    assert out["hookEventName"] == "SessionStart"
    assert "bash scripts/install.sh" in out["additionalContext"]
    assert "\n" not in out["additionalContext"]


def test_current_is_quiet():
    home, path, head = setup()
    marketplace(home, path)
    installed(home, entry(head))
    assert run(home) == ""


def test_user_entry_wins_over_a_newer_project_entry():
    # install.sh refreshes the user entry only; project entries keep the sha of their last install.
    home, path, head = setup()
    marketplace(home, path)
    installed(home, entry(head), entry("a" * 40, scope="project", updated="2026-11-04T00:00:00Z"))
    assert run(home) == ""


def test_project_only_install_uses_the_newest_entry():
    home, path, head = setup()
    marketplace(home, path)
    installed(home, entry("a" * 40, scope="project"), entry(head, scope="project", updated="2026-11-04T00:00:00Z"))
    assert run(home) == ""


def test_missing_files_are_quiet():
    home, path, _ = setup()
    assert run(home) == ""  # neither file
    marketplace(home, path)
    assert run(home) == ""  # no installed_plugins.json


def test_missing_values_are_quiet():
    home, path, head = setup()
    marketplace(home, path)
    installed(home, {"scope": "user"})  # a local-folder install records no sha
    assert run(home) == ""
    installed(home, entry("a" * 40))
    write_json(home, "known_marketplaces.json", {"other": {}})  # no harness marketplace
    assert run(home) == ""
    marketplace(home, os.path.join(home, "gone"))  # clone location gone
    assert run(home) == ""


def test_folder_marketplace_is_quiet():
    home, path, _ = setup()
    marketplace(home, path, source="directory")
    installed(home, entry("a" * 40))
    assert run(home) == ""


def test_corrupt_json_is_quiet():
    home, path, _ = setup()
    marketplace(home, path)
    os.makedirs(os.path.join(home, ".claude", "plugins"), exist_ok=True)
    with open(os.path.join(home, ".claude", "plugins", "installed_plugins.json"), "w") as f:
        f.write("{not json")
    assert run(home) == ""


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"stale-install tests: {len(tests)} passed")
