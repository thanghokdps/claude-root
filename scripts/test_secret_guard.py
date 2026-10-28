#!/usr/bin/env python3
"""Tests for plugins/core/hooks/secret-guard.sh (and its list as used by sensitive-path.sh).
Run: python3 scripts/test_secret_guard.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "plugins", "core", "hooks")
GUARD = os.path.join(HOOKS, "secret-guard.sh")
SENSITIVE = os.path.join(HOOKS, "sensitive-path.sh")


def repo():
    path = tempfile.mkdtemp(prefix="secret-guard-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    return path


def decide(hook, tool, tool_input, cwd, env=None):
    payload = json.dumps({"tool_name": tool, "cwd": cwd, "tool_input": tool_input})
    r = subprocess.run([hook], input=payload, capture_output=True, text=True, env={**os.environ, **(env or {})})
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return "allow"
    return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"]


def bash(cmd, cwd, env=None):
    return decide(GUARD, "Bash", {"command": cmd}, cwd, env)


def test_secret_files_cannot_be_read():
    cwd = repo()
    for p in [".env", "config/.env.local", "ios/AuthKey_X.p8", "android/app/release.jks", "app.keystore",
              "~/.ssh/id_rsa", "/tmp/x/.env", "keys/service-account-prod.json", "gcp/my_service_account.json"]:
        assert decide(GUARD, "Read", {"file_path": p}, cwd) == "deny", p
    assert decide(GUARD, "Edit", {"file_path": ".env"}, cwd) == "deny"
    assert decide(GUARD, "NotebookEdit", {"notebook_path": ".env"}, cwd) == "deny"


def test_bash_readers_and_copiers_are_denied():
    cwd = repo()
    for cmd in ["cat .env", "grep KEY .env", "source .env", "set -a; . .env", "base64 key.p8", "cp .env /tmp/x",
                "cat \"config/.env.local\"", "export $(cat .env)", "FOO=1 head -n1 .env", "cat < .env",
                "ls && sed -n 1,3p .env", "cat ~/.ssh/id_ecdsa", "grep -e KEY .env", "rg KEY .env"]:
        assert bash(cmd, cwd) == "deny", cmd


def test_templates_code_and_commit_messages_are_allowed():
    cwd = repo()
    assert decide(GUARD, "Read", {"file_path": ".env.example"}, cwd) == "allow"
    assert decide(GUARD, "Read", {"file_path": "src/env.ts"}, cwd) == "allow"
    for cmd in ["cat .env.example", "cat src/env.ts", "grep -rn foo src", "git commit -m \"add .env to gitignore\"",
                "git commit -m \"x; cat .env\"", "cat <<'EOF' > /dev/null\ncat .env\nEOF", "echo .env",
                "grep \".env\" .gitignore", "rg -n '.env' src"]:
        assert bash(cmd, cwd) == "allow", cmd
    assert decide(GUARD, "Glob", {"pattern": "**/*.ts"}, cwd) == "allow"
    assert decide(GUARD, "Grep", {"pattern": "x", "path": "src", "glob": "*.ts"}, cwd) == "allow"
    assert subprocess.run([GUARD], input="{}", capture_output=True, text=True).returncode == 0


def test_grep_and_glob_naming_secrets_are_denied():
    cwd = repo()
    assert decide(GUARD, "Grep", {"pattern": "KEY", "path": ".env"}, cwd) == "deny"
    assert decide(GUARD, "Grep", {"pattern": "KEY", "glob": ".env*"}, cwd) == "deny"
    assert decide(GUARD, "Grep", {"pattern": "KEY", "glob": "*.p8"}, cwd) == "deny"
    assert decide(GUARD, "Glob", {"pattern": "**/.env"}, cwd) == "deny"
    assert decide(GUARD, "Glob", {"pattern": "*.jks"}, cwd) == "deny"


def test_repo_list_extends_and_env_var_turns_off():
    cwd = repo()
    assert decide(GUARD, "Read", {"file_path": "config/master.key"}, cwd) == "deny"  # *.key already
    assert decide(GUARD, "Read", {"file_path": "config/master.pass"}, cwd) == "allow"
    os.makedirs(os.path.join(cwd, ".claude"))
    with open(os.path.join(cwd, ".claude", "secret-paths.txt"), "w") as f:
        f.write("config/master.pass\n")
    assert decide(GUARD, "Read", {"file_path": "config/master.pass"}, cwd) == "deny"
    assert bash("cat config/master.pass", cwd) == "deny"
    assert decide(GUARD, "Read", {"file_path": ".env"}, cwd, {"CLAUDE_SECRET_GUARD": "0"}) == "allow"


def test_writing_a_secret_still_asks_in_sensitive_path():
    cwd = repo()
    assert decide(SENSITIVE, "Write", {"file_path": ".env"}, cwd) == "ask"
    assert decide(SENSITIVE, "Write", {"file_path": "ios/AuthKey_X.p8"}, cwd) == "ask"
    assert decide(SENSITIVE, "Write", {"file_path": ".env.example"}, cwd) == "allow"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_secret_guard: {len(tests)} passed")
