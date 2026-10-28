#!/usr/bin/env bash
# release-gate.sh — a production release of an Expo/EAS app ships only the commit a non-author approved.
# Trigger: PreToolUse(Bash). Active when the repo has eas.json or .claude/release-gate.json; otherwise silent.
# Config .claude/release-gate.json (optional, missing keys use the defaults):
#   {"profiles":["production"],"channels":["production"],"approvers":[]}
# Denies (decision "deny", exit 0):
#   - gh pr review --approve, glab mr approve: approving is a person's decision
#   - production eas build/submit (--profile in profiles; none given = production), eas update (--channel/--branch in
#     channels, or APP_VARIANT=production), git push of a v* tag, unless a release/<version> PR (gh) or MR (glab)
#     was approved by someone other than its author (and in approvers when set) and its head or merge commit is
#     the commit being shipped; also when v<version> already sits on another commit.
#   - git push --tags (too broad to check), and any release it cannot verify (gh/glab missing or failing).
# Asks: eas update:/channel: commands (rollback, republish, rollout) on a production channel.
# This stops mistakes in a session; the real protection is who may build and publish on EAS and the stores.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import json, os, re, shlex, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
if ev.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (ev.get("tool_input") or {}).get("command") or ""
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def run(args, timeout=20, env=None):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, **env} if env else None)


try:
    r = run(["git", "rev-parse", "--show-toplevel"])
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
top = r.stdout.strip()
cwd = top
cfg_path = os.path.join(top, ".claude", "release-gate.json")
if not (os.path.exists(os.path.join(top, "eas.json")) or os.path.exists(cfg_path)):
    sys.exit(0)

cfg = {}
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except (OSError, ValueError):
    pass
profiles = cfg.get("profiles") or ["production"]
channels = cfg.get("channels") or ["production"]
approvers = cfg.get("approvers") or []

OPS = ";", "&&", "||", "|", "\n"


def segments(text):
    """Split on shell operators that sit outside quotes."""
    out, cur, quote, i = [], "", None, 0
    while i < len(text):
        ch = text[i]
        if quote:
            quote = None if ch == quote else quote
            cur += ch
        elif ch in "'\"":
            quote = ch
            cur += ch
        else:
            op = next((o for o in OPS if text.startswith(o, i)), None)
            if op:
                out.append(cur)
                cur, i = "", i + len(op)
                continue
            cur += ch
        i += 1
    return out + [cur]


def tokens(seg):
    try:
        toks = shlex.split(seg)
    except ValueError:
        toks = seg.split()
    env, i = {}, 1 if toks[:1] == ["env"] else 0
    while i < len(toks) and re.match(r"^[A-Za-z_]\w*=", toks[i]):
        k, _, v = toks[i].partition("=")
        env[k] = v
        i += 1
    return env, toks[i:]


def eas_args(toks):
    """Arguments after eas, whether run directly or through npx / pnpm dlx / bunx."""
    for i, t in enumerate(toks[:5]):
        if re.match(r"^eas(-cli)?(@\S+)?$", t) and all(p in ("npx", "pnpm", "dlx", "bunx", "yarn", "-y", "--yes") for p in toks[:i]):
            return toks[i + 1:]
    return None


def flag(args, *names):
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                return args[i + 1]
            if a.startswith(n + "="):
                return a[len(n) + 1:]
    return None


class Unverifiable(Exception):
    pass


def tool_json(args):
    try:
        r = run(args, timeout=25)
    except FileNotFoundError:
        raise Unverifiable(f"{args[0]} is not installed")
    except subprocess.TimeoutExpired:
        raise Unverifiable(f"{args[0]} timed out")
    if r.returncode != 0:
        raise Unverifiable(f"{args[0]} failed: {(r.stderr or r.stdout).strip()[:200]}")
    try:
        return json.loads(r.stdout)
    except ValueError:
        raise Unverifiable(f"{args[0]} returned invalid JSON")


def forge():
    r = run(["git", "remote", "get-url", "origin"])
    return "glab" if r.returncode == 0 and "gitlab" in r.stdout else "gh"


def allowed(login, author):
    return login and login != author and (not approvers or login in approvers)


def gh_releases(commit):
    prs = tool_json(["gh", "pr", "list", "--state", "all", "--json",
                     "number,headRefName,headRefOid,mergeCommit,author,reviews", "--limit", "100"])
    found = []
    for p in prs:
        if not str(p.get("headRefName", "")).startswith("release/"):
            continue
        head = p.get("headRefOid")
        if commit not in (head, (p.get("mergeCommit") or {}).get("oid")):
            continue
        author = (p.get("author") or {}).get("login")
        ok = any(
            rv.get("state") == "APPROVED" and allowed((rv.get("author") or {}).get("login"), author)
            and (rv.get("commit") or {}).get("oid") == head
            for rv in p.get("reviews") or []
        )
        found.append((p["headRefName"][len("release/"):], f"PR #{p.get('number')}", ok))
    return found


def glab_releases(commit):
    mrs = tool_json(["glab", "api", "projects/:id/merge_requests?state=all&per_page=50"])
    found = []
    for m in mrs:
        if not str(m.get("source_branch", "")).startswith("release/"):
            continue
        if commit not in (m.get("sha"), m.get("merge_commit_sha"), m.get("squash_commit_sha")):
            continue
        author = (m.get("author") or {}).get("username")
        appr = tool_json(["glab", "api", f"projects/:id/merge_requests/{m['iid']}/approvals"])
        ok = any(allowed((a.get("user") or {}).get("username"), author) for a in appr.get("approved_by") or [])
        found.append((m["source_branch"][len("release/"):], f"MR !{m.get('iid')}", ok))
    return found


def head_commit():
    r = run(["git", "rev-parse", "HEAD"])
    if r.returncode != 0:
        raise Unverifiable("no commit to ship")
    return r.stdout.strip()


def tag_commit(tag):
    r = run(["git", "rev-list", "-n1", f"refs/tags/{tag}"])
    return r.stdout.strip() if r.returncode == 0 else None


def check_release(commit, what, version=None, existing_tag_ok=False):
    """Return a deny reason, or None when an approved release covers `commit`."""
    short = commit[:7]
    covering = (glab_releases if forge() == "glab" else gh_releases)(commit)
    if version:
        covering = [c for c in covering if c[0] == version]
    todo = (f"Open a release/{version or '<version>'} PR/MR carrying only the version and CHANGELOG change, "
            f"get a non-author{' (' + ', '.join(approvers) + ')' if approvers else ''} approval on its current head, then run again.")
    if not covering:
        return f"{what}: no release/<version> PR/MR covers commit {short}. {todo}"
    approved = [c for c in covering if c[2]]
    if not approved:
        return f"{what}: {', '.join(c[1] for c in covering)} covers commit {short} but has no approval from someone other than its author on its current head. {todo}"
    if not existing_tag_ok:
        for ver, _, _ in approved:
            other = tag_commit(f"v{ver}")
            if other and other != commit:
                return f"{what}: v{ver} already exists on commit {other[:7]}, not {short}. A changed release needs a new version and a new approval."
    return None


reasons, asks = [], []
TAG_CONFIG = re.compile(r"followtags|remote\..+\.(?:push|mirror)\b", re.I)  # remote names may hold dots


def deny(msg):
    reasons.append(msg)


def production_command(what):
    try:
        reason = check_release(head_commit(), what)
    except Unverifiable as e:
        reason = f"{what}: can't verify the release approval: {e}"
    if reason:
        deny(reason)


def eas_command(args, env):
    sub = next((a for a in args if not a.startswith("-")), None)
    if sub in ("build", "submit"):
        profile = flag(args, "--profile", "-e") or "production"
        if profile in profiles:
            production_command(f"eas {sub} --profile {profile}")
    elif sub == "update":
        channel = flag(args, "--channel", "--branch")
        if channel in channels or env.get("APP_VARIANT") == "production":
            production_command("eas update")
    elif sub and sub.startswith(("update:", "channel:")) and sub not in ("update:list", "update:view", "channel:list", "channel:view"):
        # Rollback, republish or rollout on the production channel is an emergency path: a person confirms it.
        if any(a in channels for a in args) or env.get("APP_VARIANT") == "production":
            asks.append(f"eas {sub} changes what production users get; confirm it is the intended rollback or rollout.")


def push_command(args, gitopts=(), env=None):
    pos = [a for a in args if not a.startswith("-")]
    broad = [a for a in ("--tags", "--mirror", "--follow-tags") if a in args]
    if broad:
        deny(f"git push {broad[0]} can publish release tags that were never approved: push the one tag: git push origin v<version>")
        return
    # Push refspecs, mirror or followTags already in the config act on a plain `git push` too: read them with
    # the push's own -C/-c and GIT_* environment, so the check sees the config the push will use.
    # Only -C reaches the subprocess; env and other -c overrides were denied before we get here.
    copts = [t for j, o in enumerate(gitopts) if o == "-C" and j + 1 < len(gitopts) for t in (o, gitopts[j + 1])]
    r = run(["git", *copts, "config", "--get-regexp", r"^(remote\..*\.(push|mirror)|push\.followtags)$"])
    if r.returncode == 0 and r.stdout.strip() and not all(l.split()[-1].lower() == "false" for l in r.stdout.splitlines()):
        deny("this repo's git config sets remote.*.push, remote.*.mirror or push.followTags, so a push may publish "
             "release tags: a person pushes from here, or removes that setting first.")
        return
    for ref in pos[1:]:
        if re.search(r"[*?\[]", ref):  # refs/*:refs/* or *:* reach tags too, so any wildcard is too broad
            deny(f"git push {ref} can publish release tags that were never approved: push the one tag: git push origin v<version>")
            continue
        # A refspec src:dst publishes src under dst, so the tag's name comes from dst and its commit from src.
        src, _, dst = ref.lstrip("+").partition(":") if ":" in ref else (ref.lstrip("+"), "", ref.lstrip("+"))
        name = dst.rsplit("/", 1)[-1]
        # Anything but refs/heads/… with a v<digit> last part may land as a tag on the remote (tags/v1, refs/v1).
        if not re.match(r"^v\d", name) or dst.startswith("refs/heads/"):
            continue
        if not src or "--delete" in args or "-d" in args:
            deny(f"git push :{dst} deletes release tag {name}; a person does that by hand.")
            continue
        r = run(["git", "rev-parse", "--verify", "--quiet", f"{src}^{{commit}}"])
        commit = r.stdout.strip() if r.returncode == 0 else None
        if not commit:
            deny(f"git push {ref}: can't resolve {src} to a commit, so the release approval can't be checked.")
            continue
        try:
            reason = check_release(commit, f"git push {name}", version=name[1:], existing_tag_ok=True)
        except Unverifiable as e:
            reason = f"git push {name}: can't verify the release approval: {e}"
        if reason:
            deny(reason)


SHELLS = {"eval", "source", ".", "sh", "bash", "zsh", "dash", "ksh", "fish"}
RUNNERS = {"sudo", "doas", "nice", "ionice", "nohup", "time", "timeout", "env", "command", "builtin", "exec", "xargs",
           "parallel", "find", "stdbuf", "caffeinate", "watch"}  # run the next word as a command
# git as a word inside another program's argument (python -c "…git push…", perl -e, node -e, osascript): `.git`
# and `.gitignore` are paths, not the command.
GIT_WORD = re.compile(r"(?:^|[\s'\"/;(`$|&])git(?=$|[\s'\";)`|&])")
INFO = {"which", "type", "whereis", "man", "echo", "printf", "brew", "apt", "apt-get", "grep", "rg"}  # name git, don't run it
VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env", "--attr-source"}
FLAG_OPTS = {"--no-pager", "-P", "-p", "--paginate", "--bare", "--no-replace-objects", "--literal-pathspecs",
             "--glob-pathspecs", "--noglob-pathspecs", "--icase-pathspecs", "--no-optional-locks", "--no-advice",
             "--no-lazy-fetch"}
BUILTINS = set("add am apply archive bisect blame branch cat-file check-ignore checkout cherry-pick clean clone commit "
               "config describe diff fetch for-each-ref format-patch gc grep hash-object help init log ls-files "
               "ls-remote ls-tree merge merge-base mv notes pull push rebase reflog remote reset restore rev-list "
               "rev-parse revert rm shortlog show show-ref stash status submodule switch symbolic-ref tag "
               "update-index version worktree lfs".split())


def git_subcommand(toks):
    """Index of git's subcommand, past every global option (those in VALUE_OPTS take the next word)."""
    i = 1
    while i < len(toks) and toks[i].startswith("-"):
        i += 2 if toks[i] in VALUE_OPTS else 1
    return i


def is_git(tok):
    return os.path.basename(tok.strip("$(){}`")) == "git"


segs, pushes, wrapped = segments(cmd), False, False
for seg in segs:
    env, toks = tokens(seg)
    if not toks:
        continue
    if is_git(toks[0]):
        toks[0] = "git"
        if toks[git_subcommand(toks):][:1] == ["push"]:
            pushes = True
    elif (toks[0] not in INFO and any(is_git(t) or GIT_WORD.search(t) for t in toks[1:])) or \
            any(t.startswith(("$(", "`", "(")) and is_git(t) for t in toks[1:]):
        # git run through something (sudo -u x git, xargs git, nice -n 5 git, $(git …)): its options and the
        # wrapper's own can't be told apart, so a gated repo runs git directly.
        pushes = wrapped = True
    if toks[0] in SHELLS and any(re.search(r"\bgit\b", t) for t in toks[1:]):
        pushes = wrapped = True  # git inside a string or script the hook can't parse
    # A shell reading its commands from stdin (… | sh, bash < file, bash -s) or a command named by a variable
    # runs text the hook never sees.
    shell = os.path.basename(toks[0]) in SHELLS - {"eval", "source", "."}
    if (shell and (not any(re.match(r"^-\w*c", t) for t in toks[1:]) and len(toks) == 1
                   or any(re.match(r"^-\w*s", t) for t in toks[1:]) or "<" in seg)) \
            or toks[0].startswith("$") \
            or (os.path.basename(toks[0]) in RUNNERS and any(t.startswith("$") or os.path.basename(t) in SHELLS
                                                             for t in toks[1:])):
        pushes = wrapped = True
# A pipe into a shell (… | sh, … |& sudo /bin/bash -s) feeds it text the hook never sees.
RUN = r"(?:(?:\S*/)?(?:" + "|".join(sorted(RUNNERS)) + r")\b[^|;&\n]*?\s+)*"
if re.search(r"\|&?\s*" + RUN + r"(?:\S*/)?(?:sh|bash|zsh|dash|ksh|fish)\b", cmd) or \
        re.search(r"(?:^|[\s;&|(])(?:\S*/)?(?:sh|bash|zsh|dash|ksh|fish)\s*<", cmd):
    pushes = wrapped = True
# Anything run before a push in the same command (export, set -a, cd, source, eval…) can change the env or repo
# it runs in, which the checks below (in the hook's own env and cwd) can't follow: a push runs on its own.
if wrapped:
    deny("git must run directly here, not through sudo/xargs/env-style wrappers, $( ), eval or sh -c, so the "
         "release checks see the command it really runs.")
elif pushes and (len([s for s in segs if s.strip()]) > 1 or re.search(r"[{}()`!]|\$\(", cmd)):
    deny("git push must run as its own command here (no ;, &&, |, newline, subshell, $( ), eval or source around "
         "it), so the release checks see the env and repo it really runs in.")

for seg in segs:
    env, toks = tokens(seg)
    if not toks:
        continue
    if is_git(toks[0]):
        toks[0] = "git"
    if toks[0] == "gh" and toks[1:3] == ["pr", "review"] and ("--approve" in toks or "-a" in toks):
        deny("gh pr review --approve: approving is a person's decision. Ask the reviewer to approve it on GitHub.")
    elif toks[0] == "glab" and toks[1:3] == ["mr", "approve"]:
        deny("glab mr approve: approving is a person's decision. Ask the reviewer to approve it on GitLab.")
    elif toks[0] == "git":
        i = git_subcommand(toks)
        sub = toks[i] if i < len(toks) else ""
        opts = toks[1:i]
        # Only allowlisted global options, in either form (--exec-path=/x would pick another git-<sub>).
        unknown = [o for j, o in enumerate(opts) if o.startswith("-") and o.split("=", 1)[0] not in VALUE_OPTS | FLAG_OPTS
                   and not (j and opts[j - 1] in VALUE_OPTS)]
        if unknown:
            deny(f"git {unknown[0]} is a global option the release checks don't allow; run git without it.")
        elif any(re.search(r"alias\.", t, re.I) for t in opts):
            deny("git -c alias.* can turn any subcommand into a push; run the git command it stands for.")
        elif sub and sub not in BUILTINS:
            # An alias or an external git-<sub> on PATH can run a push the checks below never see.
            deny(f"git {sub} isn't a built-in git command (an alias or a git-{sub} program); run the git command it stands for.")
        # Env and config can pick another program, pager, hook or helper for any subcommand, and there are too
        # many such keys to list: in a gated repo git runs with neither set on its command line.
        if env:
            deny(f"git with {sorted(env)[0]}=… set on the command line can run another program; run git without it.")
        if any(o == "-c" or o.startswith("--config-env") for o in opts):
            deny("git -c/--config-env can make git run another program; run git without it.")
        if sub == "config" and any(re.match(r"alias\.", t, re.I) for t in toks[i + 1:]) and \
                any("push" in t or t.startswith("!") for t in toks[i + 1:]):
            deny("a git alias that pushes or runs a shell command would slip past the release checks; a person sets that by hand.")
        if toks[i:i + 1] == ["remote"] and any(t.startswith("--mirror") for t in toks[i + 1:]):
            deny("git remote --mirror makes every push mirror all refs, release tags included; a person sets that by hand.")
        if toks[i:i + 1] == ["config"] and any(TAG_CONFIG.search(t) for t in toks[i + 1:]):
            deny("git config push.followTags / remote.*.push / remote.*.mirror would make later pushes publish release tags; a person sets that by hand.")
        if toks[i:i + 1] == ["push"]:
            if any(TAG_CONFIG.search(t) for t in toks[1:i] + [v for k, v in env.items() if k.startswith("GIT_CONFIG")]):
                deny("git -c push.followTags pushes release tags along with the branch: push the one tag: git push origin v<version>")
            # Config pulled in from elsewhere can't be judged from the command line, so a push carries none.
            elif (any(re.match(r"include", t, re.I) for t in toks[1:i])
                  or any(t.startswith(("--git-dir", "--work-tree", "--exec-path", "--namespace", "--config-env"))
                         for t in toks[1:i])
                  or any(k.startswith("GIT_") or k in ("HOME", "XDG_CONFIG_HOME") for k in env)):
                deny("git push with include.path/includeIf, --git-dir/--work-tree, GIT_* or HOME/XDG_CONFIG_HOME "
                     "overrides can't be checked: push without them.")
            else:
                push_command(toks[i + 1:], toks[1:i], env)
    else:
        args = eas_args(toks)
        if args is not None:
            eas_command(args, env)

if reasons or asks:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny" if reasons else "ask",
        "permissionDecisionReason": " | ".join(reasons or asks),
    }}))
PY
exit 0
