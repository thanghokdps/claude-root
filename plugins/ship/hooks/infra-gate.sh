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
#   - those commands behind eval, sh -c, bash -c, xargs or a pipe into a shell, which the checks cannot read
# Asks: the same mutations on a non-production target or with no target named (the person picks the environment),
#   and terraform workspace select / kubectl config use-context onto a production name.
# Read-only commands (plan, validate, diff, get, describe, template, lint) pass silently.
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

OPS = ";", "&&", "||", "|", "\n"
TOOLS = ("terraform", "tofu", "kubectl", "helm")
TF_MUT = {"apply", "destroy", "import", "taint", "untaint", "state"}
KUBE_MUT = {"apply", "create", "delete", "replace", "patch", "scale", "rollout", "drain", "cordon", "uncordon", "edit", "set"}
HELM_MUT = {"install", "upgrade", "uninstall", "rollback", "delete"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish"}
reasons, asks = [], []


def deny(msg):
    reasons.append(msg)


def ask(msg):
    asks.append(msg)


def segments(text):
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


def is_prod(*values):
    return any(v and any(p in str(v).lower() for p in PROD) for v in values)


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
    sub = next((a for a in args if not a.startswith("-")), "")
    where = target_env(tool, args, env)
    label = {"prod": "a production target", "other": "a non-production target", None: "no environment named"}[where]
    if tool in ("terraform", "tofu"):
        if sub == "workspace" and args[1:2] == ["select"] and is_prod(*args[2:3]):
            ask(f"{tool} workspace select onto a production workspace: the person switches, then applies.")
        if sub not in TF_MUT:
            return
        if sub == "destroy":
            deny(f"{tool} destroy is never run from a session; a person runs it from the saved plan.")
        elif where == "prod":
            deny(f"{tool} {sub} on {label} ({', '.join(filter(None, flag(args, '-var-file', '--var-file') + [env.get('TF_WORKSPACE')]))}): production is applied by a person or the CI job on the protected branch. Hand over the command and the saved plan.")
        else:
            ask(f"{tool} {sub} on {label}: confirm the environment before it runs.")
    elif tool == "kubectl":
        if sub == "config" and args[1:2] == ["use-context"] and is_prod(*args[2:3]):
            ask("kubectl config use-context onto a production context: the person switches, then applies.")
        if sub not in KUBE_MUT:
            return
        kind = next((a for a in args[1:] if not a.startswith("-")), "")
        if sub == "delete" and kind.lower() in ("namespace", "ns", "node", "nodes", "pv", "persistentvolume", "pvc", "persistentvolumeclaim"):
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


for seg in segments(cmd):
    if not seg.strip():
        continue
    env, toks = tokens(seg)
    if not toks:
        continue
    head = os.path.basename(toks[0])
    body = " ".join(toks[1:])
    if any(re.search(rf"\b{t}\b", body) for t in TOOLS):
        if head == "eval" or head == "xargs" or (head in SHELLS and any(a in ("-c", "-lc", "-ic") for a in toks[1:3])):
            deny(f"{head} hides a terraform/kubectl/helm command from the gate; run it directly.")
            continue
    if head in SHELLS and any(re.search(rf"\b{t}\b", seg) for t in TOOLS) and any(a in ("-c", "-lc", "-ic") for a in toks[1:3]):
        deny(f"{head} -c hides a terraform/kubectl/helm command from the gate; run it directly.")
        continue
    if head in TOOLS:
        gate(head, toks[1:], env)
    elif head in ("npx", "pnpm", "bunx") and len(toks) > 1 and os.path.basename(toks[1]) in TOOLS:
        gate(os.path.basename(toks[1]), toks[2:], env)

if reasons or asks:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny" if reasons else "ask",
        "permissionDecisionReason": " | ".join(reasons or asks),
    }}))
PY
exit 0
