#!/usr/bin/env python3
"""Tests for core sensitive-path.sh, core compact-advisor.sh and dev auto-decisions.sh.
Run: python3 scripts/test_thunderkds_hooks.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SENSITIVE = os.path.join(ROOT, "plugins", "core", "hooks", "sensitive-path.sh")
COMPACT = os.path.join(ROOT, "plugins", "core", "hooks", "compact-advisor.sh")
AUTO = os.path.join(ROOT, "plugins", "dev", "hooks", "auto-decisions.sh")


def repo(branch="feat/7-pin-chat", plan=None):
    path = tempfile.mkdtemp(prefix="tk-hooks-")
    subprocess.run(["git", "-C", path, "init", "-q", "-b", branch], check=True)
    if plan is not None:
        os.makedirs(os.path.join(path, "docs", "tickets", "7"))
        with open(os.path.join(path, "docs", "tickets", "7", "plan.md"), "w") as f:
            f.write(plan)
    return path


def run(hook, payload, env=None):
    r = subprocess.run([hook], input=json.dumps(payload), capture_output=True, text=True,
                       env={**os.environ, "TMPDIR": tempfile.mkdtemp(), **(env or {})})
    return r.returncode, r.stdout


def asks(path, tool, **ti):
    code, out = run(SENSITIVE, {"cwd": path, "tool_name": tool, "tool_input": ti})
    assert code == 0, out
    return bool(out) and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "ask"


def test_sensitive_edits_ask():
    path = repo()
    for f in [".env", "apps/web/.env.local", "certs/server.pem", ".github/workflows/ci.yml",
              ".claude/settings.json", "Dockerfile", "infra/main.tf"]:
        assert asks(path, "Edit", file_path=os.path.join(path, f)), f


def test_ordinary_and_example_files_pass():
    path = repo()
    for f in ["src/app.ts", ".env.example", "docs/env.md", "src/server/deploy-notes.ts", "README.md"]:
        assert not asks(path, "Write", file_path=os.path.join(path, f)), f


def test_shell_writes_to_sensitive_paths_ask():
    path = repo()
    assert asks(path, "Bash", command="echo KEY=1 >> .env")
    assert asks(path, "Bash", command="cp /tmp/ci.yml .github/workflows/ci.yml")
    assert not asks(path, "Bash", command="cat .env.example > /tmp/x")
    assert not asks(path, "Bash", command="git commit -m 'edit .env > docs'")


def test_path_in_ticket_plan_is_pre_approved():
    path = repo(plan="Risk: high\nSkills: /api-endpoint\n\nFiles: .github/workflows/ci.yml\n")
    assert not asks(path, "Edit", file_path=os.path.join(path, ".github/workflows/ci.yml"))
    assert asks(path, "Edit", file_path=os.path.join(path, ".env"))


def test_repo_list_adds_and_off_switch():
    path = repo()
    os.makedirs(os.path.join(path, ".claude"))
    with open(os.path.join(path, ".claude", "sensitive-paths.txt"), "w") as f:
        f.write("db/seed-prod.sql\n")
    assert asks(path, "Edit", file_path=os.path.join(path, "db/seed-prod.sql"))
    code, out = run(SENSITIVE, {"cwd": path, "tool_name": "Edit", "tool_input": {"file_path": ".env"}},
                    env={"CLAUDE_SENSITIVE_PATHS": "0"})
    assert code == 0 and not out


def transcript(tokens):
    path = os.path.join(tempfile.mkdtemp(), "t.jsonl")
    with open(path, "w") as f:
        f.write(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
        f.write(json.dumps({"type": "assistant", "message": {"usage": {
            "input_tokens": 10, "cache_read_input_tokens": tokens, "cache_creation_input_tokens": 0}}}) + "\n")
    return path


def test_compact_advice_only_past_the_limit_and_once_per_step():
    tmp = tempfile.mkdtemp()
    env = {"TMPDIR": tmp}
    assert run(COMPACT, {"session_id": "a", "transcript_path": transcript(50_000)}, env)[1] == ""
    out = run(COMPACT, {"session_id": "a", "transcript_path": transcript(250_000)}, env)[1]
    assert "systemMessage" in out and "250k" in out
    assert run(COMPACT, {"session_id": "a", "transcript_path": transcript(260_000)}, env)[1] == ""
    assert "systemMessage" in run(COMPACT, {"session_id": "a", "transcript_path": transcript(360_000)}, env)[1]


PLAN = "Risk: {risk}\nSkills: /api-endpoint\n{section}"


def stop(path, mode="auto", active=False):
    code, out = run(AUTO, {"cwd": path, "permission_mode": mode, "stop_hook_active": active})
    assert code == 0
    return json.loads(out)["decision"] if out else "allow"


def test_auto_high_risk_without_record_blocks_once():
    path = repo(plan=PLAN.format(risk="high", section=""))
    assert stop(path) == "block"
    assert stop(path, active=True) == "allow"


def test_entries_need_a_challenge():
    path = repo(plan=PLAN.format(risk="high", section="## Auto decisions\n- chose the click · options: a / b\n"))
    assert stop(path) == "block"
    ok = "## Auto decisions\n- chose the click · options: a / b · challenged: b audits → kept\n\n## Deviations\n"
    assert stop(repo(plan=PLAN.format(risk="high", section=ok))) == "allow"
    assert stop(repo(plan=PLAN.format(risk="high", section="## Auto decisions\n- none: user answered all\n"))) == "allow"


def test_auto_decisions_skip_normal_risk_default_mode_and_other_branches():
    assert stop(repo(plan=PLAN.format(risk="normal", section=""))) == "allow"
    assert stop(repo(plan=PLAN.format(risk="high", section="")), mode="default") == "allow"
    assert stop(repo(branch="feat/no-ticket")) == "allow"


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"thunderkds hooks: {len(tests)} tests passed")
