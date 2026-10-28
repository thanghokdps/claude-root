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


def run(args, timeout=20):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout)


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
            and (rv.get("commit") is None or rv["commit"].get("oid") == head)
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


def push_command(args):
    pos = [a for a in args if not a.startswith("-")]
    if "--tags" in args:
        deny("git push --tags can publish release tags that were never approved: push the one tag: git push origin v<version>")
        return
    for ref in pos[1:]:
        name = re.sub(r"^refs/tags/", "", ref.split(":")[-1])
        if ref.startswith(":") or not name.startswith("v"):
            continue
        commit = tag_commit(name)
        if not commit:
            continue
        try:
            reason = check_release(commit, f"git push {name}", version=name[1:], existing_tag_ok=True)
        except Unverifiable as e:
            reason = f"git push {name}: can't verify the release approval: {e}"
        if reason:
            deny(reason)


for seg in segments(cmd):
    env, toks = tokens(seg)
    if not toks:
        continue
    if toks[0] == "gh" and toks[1:3] == ["pr", "review"] and ("--approve" in toks or "-a" in toks):
        deny("gh pr review --approve: approving is a person's decision. Ask the reviewer to approve it on GitHub.")
    elif toks[0] == "glab" and toks[1:3] == ["mr", "approve"]:
        deny("glab mr approve: approving is a person's decision. Ask the reviewer to approve it on GitLab.")
    elif toks[0] == "git":
        i = 1
        while i < len(toks) and toks[i] in ("-C", "-c"):
            i += 2
        if toks[i:i + 1] == ["push"]:
            push_command(toks[i + 1:])
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
