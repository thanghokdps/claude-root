#!/usr/bin/env python3
"""Tests for plugins/dev/hooks/ticket-ledger.sh + ticket-gate.sh. Run: python3 scripts/test_ticket_gate.py"""
import json
import os
import subprocess
import tempfile

from harness_state import LIB, specs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "plugins", "dev", "hooks")

PLAN = "# 7 — Plan\n\nRisk: {risk}\nSkills: /agent-tool, /agent-frontend\n\n## Deviations\n{waivers}\n"


def contract(path, *parts):
    """The ticket's contract folder: specs/7-pin-chat/ in the repo's state dir, never in the repo."""
    return specs(path, "7-pin-chat", *parts)


def repo(branch="feat/7-pin-chat", risk="normal", waivers="", plan=True, review="Verdict: APPROVED\nRounds: 1/2\n"):
    path = tempfile.mkdtemp(prefix="ticket-gate-")
    git = lambda *a: subprocess.run(["git", "-C", path, *a], check=True, capture_output=True)
    git("init", "-q", "-b", branch)
    if plan:
        os.makedirs(contract(path))
        with open(contract(path, "plan.md"), "w") as f:
            f.write(PLAN.format(risk=risk, waivers=waivers))
        if review is not None:
            with open(contract(path, "plan-review.md"), "w") as f:
                f.write(review)
    os.makedirs(os.path.join(path, "src"))
    with open(os.path.join(path, "src", "app.ts"), "w") as f:
        f.write("export {}\n")
    git("add", "-A")
    return path


def docs_only(path):
    """Unstage the code and stage a docs/ file instead."""
    subprocess.run(["git", "-C", path, "reset", "-q", "src/app.ts"], check=True)
    os.makedirs(os.path.join(path, "docs"), exist_ok=True)
    with open(os.path.join(path, "docs", "guide.md"), "w") as f:
        f.write("# Guide\n")
    subprocess.run(["git", "-C", path, "add", "docs/guide.md"], check=True)


def run(hook, path, payload):
    payload = {"cwd": path, "session_id": "s", **payload}
    r = subprocess.run([os.path.join(HOOKS, hook)], input=json.dumps(payload), capture_output=True, text=True)
    return r.returncode, r.stderr


def skill(path, name):
    run("ticket-ledger.sh", path, {"hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": {"skill": name}})


def agent(path, model):
    run("ticket-ledger.sh", path, {"hook_event_name": "PostToolUse", "tool_name": "Agent",
                                   "tool_input": {"subagent_type": "general-purpose", "model": model}})


def gate(path, command="git commit -m 'feat: pin (#7)'"):
    return run("ticket-gate.sh", path, {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                                        "tool_input": {"command": command}})


def full_build(path):
    for s in ("agent:agent-tool", "agent-frontend", "agent-verify-turn"):
        skill(path, s)
    agent(path, "sonnet")


def test_commit_without_the_plans_skills_or_a_subagent_is_blocked():
    path = repo()
    code, err = gate(path)
    assert code == 2 and "/agent-tool" in err and "/agent-verify-turn" in err and "subagent" in err, err


def test_commit_after_the_full_build_passes():
    path = repo()
    full_build(path)
    assert gate(path)[0] == 0


def test_a_subagent_on_the_session_model_does_not_count():
    path = repo()
    for s in ("agent-tool", "agent-frontend", "agent-verify-turn"):
        skill(path, s)
    agent(path, "")
    code, err = gate(path)
    assert code == 2 and "sonnet or haiku" in err, err


def test_a_recorded_waiver_lets_the_commit_through():
    path = repo(waivers="- skip /agent-verify-turn: no model key on this machine\n- skip subagents: one-line fix\n")
    skill(path, "agent-tool")
    skill(path, "agent-frontend")
    assert gate(path)[0] == 0


def test_high_risk_pr_needs_security_and_code_review():
    path = repo(risk="high")
    full_build(path)
    skill(path, "verify-done")
    skill(path, "review-checklist")
    code, err = gate(path, "gh pr create --fill")
    assert code == 2 and "/security-review" in err and "/code-review" in err, err
    run("ticket-ledger.sh", path, {"hook_event_name": "UserPromptExpansion", "command_name": "security-review"})
    skill(path, "code-review")
    assert gate(path, "gh pr create --fill")[0] == 0
    code, _ = run("ticket-gate.sh", path, {"hook_event_name": "PreToolUse",
                                           "tool_name": "mcp__github__create_pull_request", "tool_input": {}})
    assert code == 0


def test_normal_pr_still_needs_verify_done_and_review_checklist():
    path = repo()
    full_build(path)
    code, err = gate(path, "gh pr create --fill")
    assert code == 2 and "/verify-done" in err and "/review-checklist" in err and "security" not in err, err


def test_missing_or_unapproved_plan_review_blocks_a_code_commit():
    path = repo(review=None)
    full_build(path)
    code, err = gate(path)
    assert code == 2 and "plan-review.md is missing" in err, err
    path = repo(review="Verdict: REVISE\n\n## Round 1 — REVISE\n- T2 …\n")
    full_build(path)
    code, err = gate(path)
    assert code == 2 and "Verdict: REVISE" in err, err
    path = repo(review="**Verdict:** `approved`\n")
    full_build(path)
    assert gate(path)[0] == 0


def test_plan_review_waiver_and_docs_only_commit_pass():
    path = repo(review=None, waivers="- skip plan-review: one-line copy change\n")
    full_build(path)
    assert gate(path)[0] == 0
    path = repo(review=None)
    docs_only(path)
    assert gate(path)[0] == 0


def test_plan_without_skills_or_risk_line_is_blocked():
    path = repo()
    with open(contract(path, "plan.md"), "w") as f:
        f.write("# 7 — Plan\n")
    code, err = gate(path)
    assert code == 2 and "Skills:" in err and "Risk:" in err, err


def test_waiver_hint_names_the_plan_in_the_state_dir():
    path = repo()
    code, err = gate(path)
    assert code == 2 and contract(path, "plan.md") in err and "docs/tickets" not in err, err


def test_a_plan_inside_the_repo_is_not_a_contract():
    path = repo(plan=False)
    os.makedirs(os.path.join(path, "docs", "tickets", "7"))
    with open(os.path.join(path, "docs", "tickets", "7", "plan.md"), "w") as f:
        f.write(PLAN.format(risk="high", waivers=""))
    assert gate(path)[0] == 0


def test_contract_folder_by_id_when_the_slug_differs():
    for folder in ("ABC-12-old-slug", "ABC-12"):
        path = repo(branch="feat/ABC-12-new-slug", plan=False)
        os.makedirs(specs(path, folder))
        with open(specs(path, folder, "plan.md"), "w") as f:
            f.write("# ABC-12 — Plan\n")
        code, err = gate(path)
        assert code == 2 and "ticket ABC-12" in err and specs(path, folder, "plan.md") in err, (folder, err)
    path = repo(branch="feat/ABC-123-x", plan=False)
    os.makedirs(specs(path, "ABC-12-x"))
    with open(specs(path, "ABC-12-x", "plan.md"), "w") as f:
        f.write("# ABC-12 — Plan\n")
    assert gate(path)[0] == 0  # another ticket's folder is not this one's


def test_ticket_dir_fails_off_a_ticket_branch():
    path = repo(branch="chore/deps")
    r = subprocess.run(["bash", "-c", '. "$1" && ticket_dir "$2"', "_", LIB, path], capture_output=True, text=True)
    assert r.returncode == 1 and r.stdout == "", r.stdout


def test_docs_only_commit_other_branches_and_other_commands_pass():
    path = repo()
    docs_only(path)
    assert gate(path)[0] == 0
    assert gate(repo(branch="chore/deps"))[0] == 0
    assert gate(repo(plan=False))[0] == 0
    assert gate(repo(), "git status")[0] == 0
    assert gate(repo(), "echo 'git commit'")[0] == 0


def test_ledger_entries_from_another_branch_do_not_count():
    path = repo()
    full_build(path)
    subprocess.run(["git", "-C", path, "checkout", "-q", "-b", "feat/7-pin-chat-v2"], check=True)
    assert gate(path)[0] == 2


SPEC = ("# 7 — Spec\n\n## Concerns\n| C# | Between | Severity | Owner | Question | Decision |\n"
        "|----|---------|----------|-------|----------|----------|\n{rows}\n\n## Decisions\n{decisions}\n\n## Changes\n"
        "- (agent) not a decision\n")


def ready_repo(rows, decisions="- none", **kw):
    path = repo(**kw)
    full_build(path)
    with open(contract(path, "spec.md"), "w") as f:
        f.write(SPEC.format(rows=rows, decisions=decisions))
    return path


def test_open_blocking_concern_blocks_a_code_commit():
    path = ready_repo("| C1 | design ↔ API | **blocking** | backend | Which field? Recommended: id | |\n"
                      "| C2 | ticket ↔ app | `Blocking` | PO | Scope? Recommended: no | — |")
    code, err = gate(path)
    assert code == 2 and "C1 is blocking and has no decision" in err and "C2 is blocking" in err, err


def test_answered_or_waived_blocking_concern_passes():
    row = "| C1 | design ↔ API | blocking | backend | Which field? Recommended: id | 2026-01-02 use id (PO) |"
    assert gate(ready_repo(row))[0] == 0
    open_row = row.replace("2026-01-02 use id (PO)", "")
    assert gate(ready_repo(open_row, waivers="- skip concerns: PO away, assumed id\n"))[0] == 0


def test_decide_and_note_concerns_do_not_block():
    path = ready_repo("| C1 | design ↔ app | decide | dev | Reuse Card? Recommended: yes | |\n"
                      "| C2 | ticket ↔ design | note | design | Icon differs. Recommended: keep | |")
    assert gate(path)[0] == 0


def test_agent_decision_without_why_or_revert_blocks_a_code_commit():
    path = ready_repo("", decisions="- 2026-01-02 Reuse Card? → yes (agent) · why: Card.tsx:4 fits\n"
                                    "- 2026-01-02 Sort order? → newest first (agent)")
    code, err = gate(path)
    assert code == 2 and err.count("has no why:/revert:") == 2 and "Reuse Card?" in err, err


def test_agent_decision_with_note_and_user_decision_pass():
    notes = ("- 2026-01-02 Reuse Card? → yes (agent) · why: Card.tsx:4 fits · revert: inline the markup\n"
             "- 2026-01-02 Which field? → id (user)")
    assert gate(ready_repo("", decisions=notes))[0] == 0
    bare = "- 2026-01-02 Sort order? → newest first (agent)"
    assert gate(ready_repo("", decisions=bare, waivers="- skip concerns: spike branch\n"))[0] == 0


def test_docs_only_commit_ignores_an_open_blocking_concern():
    path = ready_repo("| C1 | design ↔ API | blocking | backend | Which field? Recommended: id | |")
    docs_only(path)
    assert gate(path)[0] == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_ticket_gate: {len(tests)} passed")
