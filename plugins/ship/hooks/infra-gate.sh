#!/usr/bin/env bash
# infra-gate.sh — production infrastructure is applied by a person, never from a session.
# Trigger: PreToolUse(Bash). Active when the repo holds *.tf, k8s/ or manifests/, Chart.yaml, kustomization.yaml,
# or .claude/infra-gate.json; otherwise silent. The hook lives in ship, not in the devops pack, because a gate must run
# before the pack is enabled.
# Config .claude/infra-gate.json (optional, missing keys use the defaults):
#   {"production": ["prod", "production", "live"]}   — substrings that mark a workspace, var-file, context or namespace
# Denies (decision "deny", exit 0):
#   - terraform/tofu apply|destroy, kubectl apply|create|delete|replace|patch|scale|rollout|drain|cordon, helm
#     install|upgrade|uninstall|rollback on a production workspace, var-file, context or namespace
#   - terraform destroy anywhere, kubectl delete namespace|node|pv anywhere
#   - those commands behind eval, sh -c, bash -c or xargs, which the checks cannot read; terraform apply -destroy
# Asks: the same mutations on a non-production target or with no target named (the person picks the environment),
#   terraform workspace select / kubectl config use-context onto a production name, terraform plan -destroy, and any
#   segment the gate cannot parse but that names a tool: a script (bash x.sh, source), a pipe into a shell, make or an
#   unknown wrapper. Known wrappers (sudo, timeout, nohup, command, npx, pnpm exec…) are peeled and the tool is checked;
#   flag values (-n prod, --context x) are never read as the subcommand. Segments split on ; && || | & newline ( ) { } $( `.
# Read-only commands (plan, validate, diff, get, describe, template, lint) pass silently, as do inert programs
#   (echo, cat, grep, git …) whose arguments merely mention a tool.
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY'
import glob, json, os, re, shlex, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
if ev.get("tool_name") != "Bash":
    sys.exit(0)
cmd = (ev.get("tool_input") or {}).get("command") or ""
cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
try:
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=10)
except (OSError, subprocess.SubprocessError):
    sys.exit(0)
if r.returncode != 0:
    sys.exit(0)
top = r.stdout.strip()


def at(*p):
    return os.path.join(top, *p)


cfg_path = at(".claude", "infra-gate.json")
active = (os.path.exists(cfg_path) or glob.glob(at("*.tf")) or glob.glob(at("*", "*.tf")) or glob.glob(at("*", "*", "*.tf"))
          or os.path.isdir(at("k8s")) or os.path.isdir(at("manifests")) or os.path.exists(at("Chart.yaml"))
          or glob.glob(at("*", "Chart.yaml")) or os.path.exists(at("kustomization.yaml")))
if not active:
    sys.exit(0)
cfg = {}
try:
    with open(cfg_path) as f:
        cfg = json.load(f)
except (OSError, ValueError):
    pass
PROD = [str(p).lower() for p in (cfg.get("production") or ["prod", "production", "live"])]

# Longer operators first, so "&&" and "||" are not read as "&" / "|". Subshells and substitutions become segments too.
OPS = "&&", "||", "$(", ";", "|", "&", "\n", "(", ")", "{", "}", "`"
TOOLS = ("terraform", "tofu", "kubectl", "helm")
TF_MUT = {"apply", "destroy", "import", "taint", "untaint", "state"}
KUBE_MUT = {"apply", "create", "delete", "replace", "patch", "scale", "rollout", "drain", "cordon", "uncordon", "edit", "set"}
HELM_MUT = {"install", "upgrade", "uninstall", "rollback", "delete"}
MUT = TF_MUT | KUBE_MUT | HELM_MUT
READ_ONLY = {"plan", "validate", "fmt", "show", "output", "init", "graph", "providers", "version", "diff", "get", "describe",
             "logs", "template", "lint", "status", "history", "list", "search", "repo", "dependency", "package", "pull",
             "explain", "api-resources", "api-versions", "top", "events", "cluster-info", "test", "verify", "env", "console",
             "completion", "metadata", "modules", "login", "logout", "wait", "port-forward", "exec", "cp", "auth"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
# Flags that take the next token as their value, so that value is never mistaken for the subcommand or the resource.
VALUE_FLAGS = {"-n", "--namespace", "--context", "--kube-context", "--kubeconfig", "--cluster", "--user", "-chdir",
               "-var-file", "--var-file", "-var", "-f", "--filename", "-k", "--kustomize", "-o", "--output", "-l",
               "--selector", "--values", "--set", "--set-string", "--set-file", "--version", "--timeout", "--field-selector",
               # kubectl / helm global flags that take a value
               "--as", "--as-group", "--as-uid", "-s", "--server", "--token", "--username", "--password",
               "--certificate-authority", "--client-certificate", "--client-key", "--request-timeout", "--cache-dir",
               "--tls-server-name", "--profile", "--profile-output", "--kube-apiserver", "--kube-as-user", "--kube-as-group",
               "--kube-token", "--kube-ca-file", "--kube-tls-server-name", "--registry-config", "--repository-cache",
               "--repository-config", "--burst-limit", "--qps", "--debug-level", "--log-file", "-v", "--v",
               "--target", "-target", "-replace", "-backup", "-state", "-state-out", "-lock-timeout", "-parallelism",
               "--description", "--history-max", "--ca-file", "--cert-file", "--key-file", "--repo", "--username"}
# Programs that run the next word as a command; peeled off before the tool is looked for.
WRAPPERS = {"sudo", "command", "exec", "time", "nice", "nohup", "timeout", "stdbuf", "doas", "ionice", "caffeinate",
            "builtin", "npx", "bunx"}
# Programs that only print, read or move text: a tool name in their arguments runs nothing. find (-exec), awk (system),
# sed (e), gh/glab (aliases) and yq can run a command, so they are not here. git is inert only for GIT_SAFE subcommands
# with no -c / alias / `!` / config argument (GIT_EXEC) and no GIT_* variable on the line: rebase -x, bisect run,
# submodule foreach, difftool --extcmd and GIT_PAGER / GIT_SSH_COMMAND all run what they are given.
INERT = {"echo", "printf", "cat", "grep", "rg", "ls", "head", "tail", "less", "more", "wc", "sort", "uniq", "diff",
         "cut", "tr", "tee", "touch", "mkdir", "cp", "mv", "ln", "test", "true", "false", "which", "type", "file", "stat",
         "date", "jq", "cd", "pwd"}
GIT_SAFE = {"status", "log", "diff", "show", "add", "commit", "push", "pull", "fetch", "branch", "checkout", "switch",
            "restore", "reset", "rev-parse", "remote", "tag", "stash", "blame", "grep", "rm", "mv", "describe",
            "ls-files", "cherry-pick", "revert", "merge", "worktree", "clone", "init"}
GIT_EXEC = re.compile(r"(^|\s)(-c|--config-env\S*|alias\.\S*|!|config|--extcmd\S*|-x|--exec|-u|--upload-pack\S*"
                      r"|--receive-pack\S*|--template\S*|--exec-path\S*)(\s|$|=)")
# git's global options that take a value: skipped with their value before the subcommand is read.
GIT_VALUE_FLAGS = {"-C", "--git-dir", "--work-tree", "--namespace", "--super-prefix"}


def git_inert(args, env):
    """True when a git command line can only read, write or move text; anything that may run a program asks."""
    if any(k.startswith("GIT_") for k in env) or GIT_EXEC.search(" ".join(args)):
        return False
    sub, skip = "", False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-"):
            skip = a in GIT_VALUE_FLAGS
        else:
            sub = a
            break
    return sub in GIT_SAFE
reasons, asks = [], []


def deny(msg):
    reasons.append(msg)


def ask(msg):
    asks.append(msg)


def segments(text):
    """Split on shell operators outside quotes. Inside double quotes `$(` and backticks still start a new segment,
    parsed unquoted (`;`, `&&`, `|` split again inside) since the shell runs what they hold as a fresh command list;
    the matching `)` or backtick restores the double quote. Only single quotes suppress everything."""
    out, cur, quote, i, nest = [], "", None, 0, []
    while i < len(text):
        ch = text[i]
        if quote == '"' and (text.startswith("$(", i) or ch == "`"):
            out.append(cur)
            nest.append(")" if text.startswith("$(", i) else "`")
            cur, quote, i = "", None, i + (2 if text.startswith("$(", i) else 1)
            continue
        if quote is None and nest and ch == nest[-1]:
            out.append(cur)
            nest.pop()
            cur, quote, i = "", '"', i + 1
            continue
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


def is_prod(*values):
    return any(v and any(p in str(v).lower() for p in PROD) for v in values)


def positionals(args):
    """Arguments that are neither a flag nor the value of a flag that takes one."""
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-"):
            skip = a in VALUE_FLAGS
        else:
            out.append(a)
    return out


def unwrap(toks):
    """Peel sudo / timeout 30 / pnpm exec / npx -y … off the front and return the remaining tokens."""
    while toks:
        head = os.path.basename(toks[0])
        if head in WRAPPERS:
            toks = toks[1:]
            if head in ("timeout", "nice", "ionice", "stdbuf", "sudo", "doas", "npx", "bunx"):
                while toks and toks[0].startswith("-"):
                    toks = toks[2:] if toks[0] in ("-n", "-u", "-g", "-s", "-k", "-o", "-e", "-i", "-p", "-c") and head != "npx" else toks[1:]
                if head == "timeout" and toks:
                    toks = toks[1:]  # the duration
        elif head in ("pnpm", "npm", "yarn") and toks[1:2] and toks[1] in ("exec", "dlx", "x", "run"):
            toks = toks[2:]
            while toks and toks[0].startswith("-"):
                toks = toks[1:]
        else:
            break
    return toks


def flag(args, *names):
    found = []
    for i, a in enumerate(args):
        for n in names:
            if a == n and i + 1 < len(args):
                found.append(args[i + 1])
            elif a.startswith(n + "="):
                found.append(a[len(n) + 1:])
    return found


def target_env(tool, args, env):
    """'prod', 'other' or None (no environment named) for the segment."""
    if tool in ("terraform", "tofu"):
        values = flag(args, "-var-file", "--var-file") + [env.get("TF_WORKSPACE"), env.get("TF_VAR_environment"), env.get("TF_VAR_env")]
        values += flag(args, "-chdir") + [a for a in args if a.startswith("-var=") and "env" in a.lower()]
        named = any(values)
    elif tool == "kubectl":
        values = flag(args, "--context", "-n", "--namespace", "--kubeconfig") + [env.get("KUBECONFIG")]
        named = any(values)
    else:
        values = flag(args, "--kube-context", "-n", "--namespace", "--kubeconfig") + [env.get("KUBECONFIG"), env.get("HELM_NAMESPACE")]
        named = any(values)
    if is_prod(*values):
        return "prod"
    return "other" if named else None


def gate(tool, args, env):
    pos = positionals(args)
    sub = pos[0] if pos else ""
    where = target_env(tool, args, env)
    label = {"prod": "a production target", "other": "a non-production target", None: "no environment named"}[where]
    if tool in ("terraform", "tofu") and sub == "plan" and any(a in ("-destroy", "--destroy") for a in args):
        ask(f"{tool} plan -destroy writes a plan whose later apply tears resources down; confirm it is wanted.")
        return
    if tool == "helm" and args[:1] == ["diff"]:
        # The helm-diff plugin: `helm diff upgrade …` renders, it never applies. Only when `diff` is the very first
        # argument: behind a flag the gate does not know, `diff` may be that flag's value and `upgrade` the real verb.
        return
    if sub not in MUT and any(a in MUT for a in args):
        # A mutating verb sits somewhere the parser did not expect (an unknown flag swallowed the subcommand): fail
        # closed before any read-only shortcut, so `kubectl --odd get apply …` cannot ride on `get`.
        ask(f"{tool} command carries a mutating verb in an unexpected position; confirm what it runs.")
        return
    if sub in READ_ONLY:
        return
    if tool in ("terraform", "tofu"):
        if sub == "workspace" and pos[1:2] == ["select"] and is_prod(*pos[2:3]):
            ask(f"{tool} workspace select onto a production workspace: the person switches, then applies.")
        if sub not in TF_MUT:
            return
        if sub == "destroy" or (sub in ("apply", "plan") and any(a in ("-destroy", "--destroy") for a in args)):
            deny(f"{tool} destroy is never run from a session; a person runs it from the saved plan.")
        elif where == "prod":
            deny(f"{tool} {sub} on {label} ({', '.join(filter(None, flag(args, '-var-file', '--var-file') + [env.get('TF_WORKSPACE')]))}): production is applied by a person or the CI job on the protected branch. Hand over the command and the saved plan.")
        else:
            ask(f"{tool} {sub} on {label}: confirm the environment before it runs.")
    elif tool == "kubectl":
        if sub == "config" and pos[1:2] == ["use-context"] and is_prod(*pos[2:3]):
            ask("kubectl config use-context onto a production context: the person switches, then applies.")
        if sub not in KUBE_MUT:
            return
        kind = pos[1].split("/")[0] if pos[1:] else ""
        if sub == "delete" and kind.lower() in ("namespace", "namespaces", "ns", "node", "nodes", "no", "pv", "persistentvolume",
                                                "persistentvolumes", "pvc", "persistentvolumeclaim", "persistentvolumeclaims"):
            deny(f"kubectl delete {kind} is never run from a session; a person runs it after a review.")
        elif where == "prod":
            deny(f"kubectl {sub} on {label}: production is applied by a person or the CI job on the protected branch. Hand over the command and the kubectl diff.")
        else:
            ask(f"kubectl {sub} on {label}: confirm the context and namespace before it runs.")
    else:
        if sub not in HELM_MUT:
            return
        if where == "prod":
            deny(f"helm {sub} on {label}: production is applied by a person or the CI job on the protected branch. Hand over the command and the helm diff.")
        else:
            ask(f"helm {sub} on {label}: confirm the context and namespace before it runs.")


def mentions_tool(text):
    return any(re.search(rf"\b{t}\b", text) for t in TOOLS)


segs = [s for s in segments(cmd) if s.strip()]
whole_mentions = mentions_tool(cmd)
for seg in segs:
    try:
        shlex.split(seg)
    except ValueError:
        if mentions_tool(seg):
            # An unterminated quote: the shell's reading and the gate's may differ, so the gate does not guess.
            ask("the command has an unbalanced quote around a terraform/kubectl/helm call; the gate cannot read it — rewrite it.")
            continue
    env, raw = tokens(seg)
    if not raw:
        continue
    head = os.path.basename(raw[0])
    if head == "eval" or head == "xargs" or (head in SHELLS and any(a in ("-c", "-lc", "-ic") for a in raw[1:3])):
        if whole_mentions:
            deny(f"{head} hides a terraform/kubectl/helm command from the gate; run it directly.")
        continue
    if (head in SHELLS or head in ("source", ".")) and whole_mentions:
        # bash script.sh, source x, or a pipe whose right-hand side is a shell: the command text is not readable here.
        ask(f"{head} runs a script or stdin that mentions terraform/kubectl/helm; the gate cannot read it — confirm what it applies.")
        continue
    toks = unwrap(raw)
    if not toks:
        continue
    tool = os.path.basename(toks[0])
    if tool in TOOLS:
        gate(tool, toks[1:], env)
    elif mentions_tool(seg) and head not in INERT and not (head == "git" and git_inert(raw[1:], env)):
        # The tool name appears behind a program the gate does not know (an alias, a make target, a wrapper it did not
        # peel): fail closed rather than let an apply through unread.
        ask(f"{head} wraps a terraform/kubectl/helm command the gate cannot parse; run the tool directly.")

if reasons or asks:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny" if reasons else "ask",
        "permissionDecisionReason": " | ".join(reasons or asks),
    }}))
PY
exit 0
