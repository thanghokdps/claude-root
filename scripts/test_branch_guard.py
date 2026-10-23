#!/usr/bin/env python3
"""Tests for plugins/guards/hooks/branch-guard.sh. Run: python3 scripts/test_branch_guard.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "guards", "hooks", "branch-guard.sh")


def repo_on(branch, upstream=None, config=()):
    path = tempfile.mkdtemp(prefix="branch-guard-")
    git = lambda *a: subprocess.run(["git", "-C", path, *a], check=True, capture_output=True)
    git("init", "-q", "-b", branch)
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "init")
    if upstream:
        git("config", f"branch.{branch}.remote", "origin")
        git("config", f"branch.{branch}.merge", f"refs/heads/{upstream}")
    for key, value in config:
        git("config", "--add", key, value)
    return path


def exit_code(command, branch="feat/x", upstream=None, config=(), env_branches=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": repo_on(branch, upstream, config)}
    env.pop("HARNESS_ENV_BRANCHES", None)
    if env_branches is not None:
        env["HARNESS_ENV_BRANCHES"] = env_branches
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode


def test_force_push_to_a_protected_branch_is_blocked():
    for cmd in ["git push -f origin main", "git push --force origin master", "git push --force-with-lease origin dev",
                "git push origin +main", "git push -uf origin main", "git push origin HEAD:main --force"]:
        assert exit_code(cmd) == 2, cmd
    assert exit_code("git push --force", branch="main") == 2


def test_dash_f_inside_a_branch_name_is_not_a_force_flag():
    assert exit_code("git push -u origin feat/dev-fullstack-skills", branch="feat/dev-fullstack-skills") == 0
    assert exit_code("git push -u origin feat/agent-tool-from-api 2>&1 | tail -1") == 0


def test_flags_and_branch_names_after_the_push_belong_to_other_commands():
    assert exit_code("git push -u origin feat/x && gh pr create --base main --body-file body.md") == 0


def test_branch_merely_containing_a_protected_name_is_not_protected():
    assert exit_code("git push --force origin feat/dev-tools", branch="feat/dev-tools") == 0
    assert exit_code("git push --force origin fix/main-menu") == 0


def test_every_push_in_a_chained_command_is_checked():
    assert exit_code("git push -u origin feat/x; git push -f origin main") == 2
    assert exit_code("git push -f origin main && git push origin feat/x") == 2
    assert exit_code("git -C . push --force origin main") == 2


def test_quoted_or_unresolvable_targets_fail_closed():
    assert exit_code('git push -f origin "main"') == 2
    assert exit_code("git push -f origin 'master'") == 2
    assert exit_code("git push -f origin $BRANCH") == 2
    assert exit_code("git push --force origin `git branch --show-current`") == 2


def test_all_refs_mirror_and_deletes_reach_protected_branches():
    assert exit_code("git push --mirror origin") == 2
    assert exit_code("git push --mir origin") == 2
    assert exit_code("git push -f --all origin") == 2
    assert exit_code("git push --force --branches origin") == 2
    assert exit_code("git push origin --delete main") == 2
    assert exit_code("git push origin :main") == 2
    assert exit_code("git push origin --delete feat/old") == 0


def test_force_without_refspec_follows_the_upstream():
    assert exit_code("git push -f", branch="feat/x", upstream="main") == 2
    assert exit_code("git push -f origin", branch="feat/x", upstream="main") == 2
    assert exit_code("git push -f", branch="feat/x", upstream="feat/x") == 0


def test_option_values_are_not_counted_as_remote_or_refspec():
    assert exit_code("git push -f -o ci.skip origin", upstream="main") == 2
    assert exit_code("git push --force --push-option x origin main") == 2
    assert exit_code("git push -o ci.skip origin feat/x") == 0


def test_shell_expansions_in_a_forced_target_fail_closed():
    for target in ["{main,x}", "ma*", "mai?", "[m]ain", "~/x"]:
        assert exit_code(f"git push -f origin {target}") == 2, target


def test_configured_push_refspecs_are_checked():
    assert exit_code("git push origin", config=[("remote.origin.push", "+refs/heads/*:refs/heads/main")]) == 2
    assert exit_code("git push -f origin", config=[("remote.origin.push", "refs/heads/x:refs/heads/main")]) == 2
    assert exit_code("git -c remote.origin.push=+HEAD:main push origin") == 2
    assert exit_code("git push -f", config=[("push.default", "matching")]) == 2
    assert exit_code("git push origin", config=[("remote.origin.push", "refs/heads/feat/x:refs/heads/feat/x")]) == 0


def test_pushes_hidden_in_subshells_eval_or_aliases_fail_closed():
    assert exit_code("(git push -f origin main)") == 2
    assert exit_code("{ git push -f origin main; }") == 2
    assert exit_code("eval 'git push -f origin main'") == 2
    assert exit_code("sh -c 'git push --force origin main'") == 2
    assert exit_code("git fp origin main", config=[("alias.fp", "push -f")]) == 2
    assert exit_code("git shipit", config=[("alias.shipit", "!git push -f origin main")]) == 2
    assert exit_code("git st", config=[("alias.st", "status")]) == 0


def test_any_direct_push_to_an_environment_branch_is_blocked():
    for cmd in ["git push origin dev", "git push -u origin staging", "git push origin HEAD:prod",
                "git push origin feat/x:refs/heads/production", "git push origin stag"]:
        assert exit_code(cmd) == 2, cmd
    assert exit_code("git push", branch="dev") == 2
    assert exit_code("git push origin", branch="feat/x", upstream="stag") == 2
    assert exit_code("git push origin", config=[("remote.origin.push", "HEAD:refs/heads/prod")]) == 2


def test_environment_branch_spelled_another_way_is_still_blocked():
    assert exit_code("git push origin HEAD", branch="dev") == 2
    assert exit_code("git push -u origin @", branch="stag") == 2
    assert exit_code("git push origin feat/x:heads/prod") == 2
    assert exit_code('git push origin de"v"') == 2
    assert exit_code("git push origin $TARGET") == 2
    assert exit_code("git push --all origin", config=[("branch.dev.description", "x")]) == 0
    assert exit_code("git push origin HEAD") == 0


def test_push_of_all_branches_is_blocked_when_one_is_an_environment_branch():
    path = repo_on("feat/x")
    subprocess.run(["git", "-C", path, "branch", "dev"], check=True)
    env = {**os.environ, "CLAUDE_PROJECT_DIR": path}
    env.pop("HARNESS_ENV_BRANCHES", None)
    payload = json.dumps({"tool_input": {"command": "git push --all origin"}})
    assert subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode == 2


def run_in(path, command):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": path}
    env.pop("HARNESS_ENV_BRANCHES", None)
    payload = json.dumps({"tool_input": {"command": command}})
    return subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=env).returncode


def test_wildcard_push_config_and_mirror_remotes_count_as_pushing_everything():
    path = repo_on("feat/x", config=[("remote.origin.push", "refs/heads/*:refs/heads/*")])
    subprocess.run(["git", "-C", path, "branch", "prod"], check=True)
    assert run_in(path, "git push origin") == 2
    assert exit_code("git push origin", config=[("remote.origin.push", "refs/heads/*:refs/heads/*")]) == 0
    assert exit_code("git push origin feat/x", config=[("remote.origin.mirror", "true")]) == 2
    assert exit_code("git -c remote.origin.mirror=true push origin feat/x") == 2


def test_push_runs_in_the_repository_a_cd_or_dash_c_points_to():
    other = repo_on("dev")
    assert exit_code(f"cd {other} && git push origin HEAD") == 2
    assert exit_code(f"git -C {other} push") == 2
    assert exit_code(f"cd {other}; git push -u origin feat/x:feat/x") == 0
    assert run_in(other, f"cd {repo_on('feat/x')} && git push origin HEAD") == 0


def test_a_repository_the_guard_cannot_resolve_fails_closed():
    assert exit_code("cd - && git push") == 2
    assert exit_code("cd ~/other && git push origin HEAD") == 2
    assert exit_code("git --git-dir=/tmp/x/.git push origin feat/x") == 2
    assert exit_code("GIT_DIR=/tmp/x/.git git push") == 2
    assert exit_code("git -C $REPO push origin feat/x:feat/x") == 0


def test_a_source_only_refspec_follows_the_configured_push_mapping():
    cfg = [("remote.origin.push", "refs/heads/feat/x:refs/heads/prod")]
    assert exit_code("git push origin feat/x", config=cfg) == 2
    assert exit_code("git push origin feat/x:feat/x", config=cfg) == 0


def test_feature_branches_and_main_are_not_environment_branches():
    assert exit_code("git push -u origin feat/x") == 0
    assert exit_code("git push origin feat/prod-banner") == 0
    assert exit_code("git push", branch="main") == 0


def test_environment_branches_can_be_overridden():
    assert exit_code("git push origin qa", env_branches="qa uat") == 2
    assert exit_code("git push origin dev", env_branches="qa uat") == 0
    assert exit_code("git push origin dev", env_branches="") == 0


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_branch_guard: {len(tests)} passed")
