#!/usr/bin/env python3
"""Tests for plugins/ship/hooks/release-gate.sh. Run: python3 scripts/test_release_gate.py"""
import json
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "ship", "hooks", "release-gate.sh")

GH_STUB = '#!/bin/sh\n[ -f "$RG_DIR/gh.exit" ] && exit "$(cat "$RG_DIR/gh.exit")"\ncat "$RG_DIR/gh.json"\n'
GLAB_STUB = """#!/bin/sh
case "$2" in
  *approvals) iid=$(echo "$2" | sed 's|.*merge_requests/\\([0-9]*\\)/approvals|\\1|'); cat "$RG_DIR/glab-approvals-$iid.json" ;;
  *) cat "$RG_DIR/glab-mrs.json" ;;
esac
"""


def git(path, *a):
    return subprocess.run(["git", "-C", path, *a], check=True, capture_output=True, text=True).stdout.strip()


def commit(path, name):
    with open(os.path.join(path, name), "w") as f:
        f.write(name)
    git(path, "add", "-A")
    git(path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", f"feat: {name}")
    return git(path, "rev-parse", "HEAD")


def repo(eas=True, remote="git@github.com:acme/app.git", config=None):
    path = tempfile.mkdtemp(prefix="release-gate-")
    git(path, "init", "-q", "-b", "feat/x")
    if eas:
        with open(os.path.join(path, "eas.json"), "w") as f:
            f.write("{}")
    if config is not None:
        os.makedirs(os.path.join(path, ".claude"))
        with open(os.path.join(path, ".claude", "release-gate.json"), "w") as f:
            json.dump(config, f)
    git(path, "remote", "add", "origin", remote)
    commit(path, "a.txt")
    return path


def stubs(gh=None, glab_mrs=None, glab_approvals=None):
    d = tempfile.mkdtemp(prefix="release-gate-bin-")
    for name, body in (("gh", GH_STUB), ("glab", GLAB_STUB)):
        p = os.path.join(d, name)
        with open(p, "w") as f:
            f.write(body)
        os.chmod(p, 0o755)
    for name, data in (("gh.json", gh), ("glab-mrs.json", glab_mrs)):
        with open(os.path.join(d, name), "w") as f:
            json.dump(data if data is not None else [], f)
    for iid, data in (glab_approvals or {}).items():
        with open(os.path.join(d, f"glab-approvals-{iid}.json"), "w") as f:
            json.dump(data, f)
    return d


def gate(path, command, bin_dir=None, path_env=None):
    env = dict(os.environ)
    if bin_dir:
        env["RG_DIR"] = bin_dir
        env["PATH"] = bin_dir + os.pathsep + env["PATH"]
    if path_env:
        env["PATH"] = path_env
    payload = {"cwd": path, "session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Bash",
               "tool_input": {"command": command}}
    r = subprocess.run([HOOK], input=json.dumps(payload), capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return "allow", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


def gh_pr(sha, reviews, author="dev", name="release/1.4.0", merge=None):
    return {"number": 5, "headRefName": name, "headRefOid": sha, "mergeCommit": {"oid": merge} if merge else None,
            "author": {"login": author}, "reviews": reviews}


def approve(login, sha):
    return {"author": {"login": login}, "state": "APPROVED", "commit": {"oid": sha}}


PROD = "eas build --profile production --platform all"


def test_inactive_without_eas_json_or_config():
    path = repo(eas=False)
    assert gate(path, PROD)[0] == "allow"
    assert gate(path, "gh pr review 5 --approve")[0] == "allow"
    assert gate(tempfile.mkdtemp(), PROD)[0] == "allow"  # not a git repo


def test_dev_profiles_and_channels_pass():
    path = repo()
    assert gate(path, "eas build --profile dev --platform ios")[0] == "allow"
    assert gate(path, "eas update --channel preview --message x")[0] == "allow"
    assert gate(path, "git push origin feat/x")[0] == "allow"
    assert gate(path, "echo 'eas build --profile production'")[0] == "allow"


def test_approving_is_always_denied():
    path = repo()
    d, why = gate(path, "gh pr review 5 --approve -b ok")
    assert d == "deny" and "person's decision" in why, why
    assert gate(path, "gh pr review 5 -a")[0] == "deny"
    assert gate(path, "cd x && glab mr approve 5")[0] == "deny"
    assert gate(path, "gh pr review 5 --comment -b hi")[0] == "allow"


def test_production_without_a_covering_approved_release_is_denied():
    path = repo()
    sha = git(path, "rev-parse", "HEAD")
    for prs in ([],
                [gh_pr(sha, [approve("dev", sha)])],  # author only
                [gh_pr("0" * 40, [approve("bob", "0" * 40)])],  # other commit
                [gh_pr(sha, [approve("bob", "0" * 40)])],  # approved an older head
                [gh_pr(sha, [{"author": {"login": "bob"}, "state": "COMMENTED", "commit": {"oid": sha}}])],
                [gh_pr(sha, [approve("bob", sha)], name="feature/x")]):
        d, why = gate(path, PROD, stubs(gh=prs))
        assert d == "deny" and "release/" in why, (prs, why)


def test_production_with_a_non_author_approval_on_head_passes():
    path = repo()
    sha = git(path, "rev-parse", "HEAD")
    assert gate(path, PROD, stubs(gh=[gh_pr(sha, [approve("bob", sha)])]))[0] == "allow"
    merged = gh_pr("1" * 40, [approve("bob", "1" * 40)], merge=sha)
    assert gate(path, "eas submit --profile=production --platform ios --id abc", stubs(gh=[merged]))[0] == "allow"
    assert gate(path, "FOO=1 npx eas-cli build -e production", stubs(gh=[merged]))[0] == "allow"
    assert gate(path, "pnpm dlx eas-cli build --profile production", stubs(gh=[])) [0] == "deny"
    # glab
    gl = repo(remote="git@gitlab.com:acme/app.git")
    sha = git(gl, "rev-parse", "HEAD")
    mr = {"iid": 9, "source_branch": "release/1.4.0", "sha": sha, "merge_commit_sha": None, "squash_commit_sha": None,
          "author": {"username": "dev"}}
    ok = {"approved_by": [{"user": {"username": "bob"}}]}
    own = {"approved_by": [{"user": {"username": "dev"}}]}
    assert gate(gl, PROD, stubs(glab_mrs=[mr], glab_approvals={9: ok}))[0] == "allow"
    assert gate(gl, PROD, stubs(glab_mrs=[mr], glab_approvals={9: own}))[0] == "deny"
    assert gate(gl, PROD, stubs(glab_mrs=[{**mr, "sha": "0" * 40}], glab_approvals={9: ok}))[0] == "deny"


def test_approvers_list_restricts_who_counts():
    path = repo(config={"approvers": ["lead"]})
    sha = git(path, "rev-parse", "HEAD")
    assert gate(path, PROD, stubs(gh=[gh_pr(sha, [approve("bob", sha)])]))[0] == "deny"
    assert gate(path, PROD, stubs(gh=[gh_pr(sha, [approve("lead", sha)])]))[0] == "allow"


def test_config_changes_the_production_profiles_and_channels():
    path = repo(config={"profiles": ["store"], "channels": ["live"]})
    b = stubs(gh=[])
    assert gate(path, PROD, b)[0] == "allow"
    assert gate(path, "eas build --profile store", b)[0] == "deny"
    assert gate(path, "eas update --channel live", b)[0] == "deny"
    assert gate(path, "eas update --branch=live", b)[0] == "deny"


def test_tag_push_needs_the_release_for_that_tag():
    path = repo()
    first = git(path, "rev-parse", "HEAD")
    git(path, "tag", "v1.4.0")
    b = stubs(gh=[gh_pr(first, [approve("bob", first)])])
    assert gate(path, "git push origin v1.4.0", b)[0] == "allow"
    assert gate(path, "git push origin refs/tags/v1.4.0", b)[0] == "allow"
    d, why = gate(path, "git push --tags", b)
    assert d == "deny" and "push the one tag" in why, why
    assert gate(path, "git push origin v1.5.0", b)[0] == "deny"  # nothing to resolve: can't be checked
    assert gate(path, "git push origin HEAD:v1.5.0", b)[0] == "deny"  # may land as a tag on the remote
    assert gate(path, "git push origin HEAD:refs/heads/v1.5.0", b)[0] == "allow"
    assert gate(path, "git push --delete origin v1.4.0", b)[0] == "deny"
    assert gate(path, "git push -d origin v1.4.0", b)[0] == "deny"
    git(path, "tag", "v1.5.0")
    assert gate(path, "git push origin v1.5.0", b)[0] == "deny"  # release is for 1.4.0
    second = commit(path, "b.txt")
    git(path, "tag", "-f", "v1.4.0")  # now on a commit the approved release does not cover
    assert gate(path, "git push origin v1.4.0", b)[0] == "deny"
    assert gate(path, "git push origin feat/x", b)[0] == "allow"
    assert gate(path, f"git -C {path} push origin v1.4.0", b)[0] == "deny"
    # refspecs publish src under a tag name that need not exist locally
    assert gate(path, "git push origin HEAD:refs/tags/v1.4.0", b)[0] == "deny"
    assert gate(path, f"git push origin {first}:refs/tags/v1.4.0", b)[0] == "allow"
    assert gate(path, "git push origin nope:refs/tags/v1.4.0", b)[0] == "deny"
    assert gate(path, "git push origin :refs/tags/v1.4.0", b)[0] == "deny"
    for flag in ("--mirror", "--follow-tags"):
        assert gate(path, f"git push {flag} origin", b)[0] == "deny", flag
    assert gate(path, "git push origin 'refs/tags/*:refs/tags/*'", b)[0] == "deny"
    assert gate(path, "git -c push.followTags=true push origin main", b)[0] == "deny"
    assert gate(path, "git push origin 'refs/*:refs/*'", b)[0] == "deny"
    assert gate(path, "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push origin main",
                b)[0] == "deny"
    assert gate(path, "git config push.followTags true", b)[0] == "deny"
    assert gate(path, "git config remote.origin.push 'refs/tags/*:refs/tags/*'", b)[0] == "deny"
    assert gate(path, "git -c remote.origin.mirror=true push origin main", b)[0] == "deny"
    assert gate(path, "git push origin HEAD:tags/v1.5.0", b)[0] == "deny"
    assert gate(path, "git config remote.my.fork.push 'refs/tags/*'", b)[0] == "deny"
    assert gate(path, "git remote add --mirror=push backup git@x:y.git", b)[0] == "deny"
    git(path, "config", "remote.origin.push", "refs/tags/*:refs/tags/*")
    assert gate(path, "git push origin feat/x", b)[0] == "deny"
    git(path, "config", "--unset", "remote.origin.push")
    assert gate(path, "git push origin feat/x", b)[0] == "allow"
    assert gate(path, "git -c include.path=/tmp/x.cfg push origin feat/x", b)[0] == "deny"
    assert gate(path, "GIT_CONFIG_GLOBAL=/tmp/x.cfg git push origin feat/x", b)[0] == "deny"
    assert gate(path, "GIT_DIR=/tmp/other.git git push origin feat/x", b)[0] == "deny"
    assert gate(path, "HOME=/tmp/h git push origin feat/x", b)[0] == "deny"
    assert gate(path, "GIT_TRACE=1 git push origin feat/x", b)[0] == "deny"
    for cmd in ["export GIT_DIR=/tmp/o.git; git push origin feat/x", "set -a; HOME=/tmp/h; git push origin feat/x",
                "declare -x XDG_CONFIG_HOME=/tmp/c && git push origin feat/x", "cd /tmp/other && git push origin v1.4.0",
                "export FOO=1\ngit push origin feat/x", "{ cd /tmp; git push origin feat/x; }", "(git push origin feat/x)",
                "eval git push origin feat/x", "echo $(git push origin feat/x)", "source x.sh && git push origin feat/x"]:
        assert gate(path, cmd, b)[0] == "deny", cmd
    assert gate(path, "git push origin feat/x", b)[0] == "allow"
    assert gate(path, "cd /tmp && ls", b)[0] == "allow"
    assert gate(path, "git add a.ts && git commit -m \"feat: push notifications (#12)\"", b)[0] == "allow"
    for cmd in ["cd /tmp; \"git\" push origin feat/x", "cd /tmp; g\\it push origin feat/x",
                "cd /tmp; git --no-pager push origin feat/x", "cd /tmp; command git push origin feat/x",
                "bash -c 'git push origin feat/x'", "git --no-pager push --tags",
                "git --git-dir=/tmp/o.git push origin feat/x", "git -P push origin HEAD:refs/tags/v9.0.0"]:
        assert gate(path, cmd, b)[0] == "deny", cmd
    assert gate(path, "git --no-pager push origin feat/x", b)[0] == "allow"
    for cmd in ["git --git-dir /tmp/o.git push origin feat/x", "git --work-tree /tmp/w push origin feat/x",
                "git -c alias.p=push p origin v1.4.0", "sudo -u bob git push origin feat/x",
                "nice -n 5 git push origin feat/x", "/usr/bin/git push --tags", "xargs git push < refs.txt",
                "sh -c 'git p origin v1.4.0'", "eval \"git $SUB origin\"",
                "git config alias.ship '!git push --tags'"]:
        assert gate(path, cmd, b)[0] == "deny", cmd
    git(path, "config", "alias.p", "push")
    assert gate(path, "git p origin v1.4.0", b)[0] == "deny"
    git(path, "config", "--unset", "alias.p")
    other = repo()
    git(other, "config", "alias.p", "push")
    for cmd in [f"git -C {other} p origin v1.4.0", "git -c x.y=1 p origin", "GIT_CONFIG_GLOBAL=/tmp/g git p",
                "git --attr-source HEAD push origin v9.9.9", "git --weird-opt push origin feat/x",
                "find . -exec git push \\;", "xargs -I{} git", "cat cmds.txt | sh", "bash < cmds.txt",
                "bash -s", "$GIT push origin feat/x", "cat x | /bin/sh", "bash -xs < cmds.txt", "/bin/bash<cmds.txt",
                "sudo $G push origin feat/x", "git --exec-path=/tmp/x push origin feat/x", "git flow release finish",
                "PATH=/tmp/x:$PATH git status", "sudo bash -c 'git push --tags'", "cat x |& sudo /bin/bash",
                "cat x | nice -n 5 sh", "GIT_EXEC_PATH=/tmp git status", "PAGER=/tmp/p git log",
                "git -c core.pager=/tmp/p log", "git -c core.hooksPath=/tmp/h commit -m x",
                "git --config-env=core.sshCommand=SSH fetch", "git -c gpg.program=/tmp/x commit -m x",
                "git -c diff.x.command=/tmp/x diff", "EDITOR=/tmp/x git commit", "LD_PRELOAD=/tmp/x.so git status",
                "python3 -c \"import os; os.system('git push --tags')\"", "perl -e 'system(\"git push\")'",
                "node -e \"require('child_process').execSync('git push')\"", "busybox sh -c 'git push'",
                "python3 -c \"import os; os.system('g'+'it pu'+'sh')\"", "ruby -e 'system %w[g i t].join'",
                "awk 'BEGIN{system(\"gi\" \"t push\")}'", "/usr/bin/python3 -c 'print(1)'",
                "python3 -Wignore -c 'print(1)'", "python3 -Ic 'print(1)'", "node --eval=1", "sudo node -e 1",
                "env python3 -c 1", "cat x.py | python3", "python3 - < x.py", "python3 < x.py", "node",
                "python3 missing.py", "python3 -Wd -Ic 1", "node --input-type=module -", "node -r ./x.js",
                "NODE_OPTIONS='--require /tmp/x.js' node scripts/build.js", "python3.12 -c 1", "pypy3 -c 1",
                "ts-node -e 1", "vim -c '!git push' x", "emacs --eval '(shell-command \"git push\")'",
                "python3 /tmp/outside.py"]:
        assert gate(path, cmd, b)[0] == "deny", cmd
    os.makedirs(os.path.join(path, "scripts"))
    for name in ("gen.py", "build.js"):
        open(os.path.join(path, "scripts", name), "w").close()
    for cmd in ["git status", "git log --oneline -3", "which git", "brew install git", "git lfs pull",
                "bash scripts/build.sh", "cat .gitignore", "ls .git", "npm run test", "python3 scripts/gen.py",
                "node scripts/build.js", "node --version", "python3 -V"]:
        assert gate(path, cmd, b)[0] == "allow", cmd
    other = repo()
    git(other, "config", "remote.origin.push", "refs/tags/*:refs/tags/*")
    assert gate(path, f"git -C {other} push origin feat/x", b)[0] == "deny"  # config read where the push runs
    assert second != first


def test_review_without_its_commit_does_not_count():
    path = repo()
    sha = git(path, "rev-parse", "HEAD")
    review = {"author": {"login": "bob"}, "state": "APPROVED"}
    assert gate(path, PROD, stubs(gh=[gh_pr(sha, [review])]))[0] == "deny"


def test_production_channel_rollback_asks():
    path = repo()
    b = stubs(gh=[])
    assert gate(path, "eas update:rollback --channel production", b)[0] == "ask"
    assert gate(path, "eas update:republish --group abc --branch production", b)[0] == "ask"
    assert gate(path, "eas update:rollback --channel preview", b)[0] == "allow"
    assert gate(path, "eas update:list --branch production", b)[0] == "allow"


def test_existing_version_tag_on_another_commit_denies_the_build():
    path = repo()
    first = git(path, "rev-parse", "HEAD")
    git(path, "tag", "v1.4.0")
    head = commit(path, "b.txt")
    d, why = gate(path, PROD, stubs(gh=[gh_pr(head, [approve("bob", head)])]))
    assert d == "deny" and "v1.4.0" in why and first[:7] in why, why


def test_ota_to_production_and_unverifiable_releases_are_denied():
    path = repo()
    sha = git(path, "rev-parse", "HEAD")
    empty = stubs(gh=[])
    assert gate(path, "APP_VARIANT=production eas update --channel production", empty)[0] == "deny"
    assert gate(path, "env APP_VARIANT=production eas update --channel staging", empty)[0] == "deny"
    assert gate(path, "eas update --channel production", empty)[0] == "deny"
    approved = stubs(gh=[gh_pr(sha, [approve("bob", sha)])])
    assert gate(path, "APP_VARIANT=production eas update --channel production", approved)[0] == "allow"
    # gh failing, returning junk, or absent
    failing = stubs(gh=[])
    with open(os.path.join(failing, "gh.exit"), "w") as f:
        f.write("1")
    d, why = gate(path, PROD, failing)
    assert d == "deny" and "can't verify the release approval" in why, why
    junk = stubs()
    with open(os.path.join(junk, "gh.json"), "w") as f:
        f.write("not json")
    assert "can't verify" in gate(path, PROD, junk)[1]
    bare = tempfile.mkdtemp(prefix="release-gate-path-")
    for tool in ("bash", "python3", "git", "cat", "env"):
        os.symlink(shutil.which(tool), os.path.join(bare, tool))
    d, why = gate(path, PROD, path_env=bare)
    assert d == "deny" and "can't verify the release approval" in why and "gh" in why, why


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_release_gate: {len(tests)} passed")
