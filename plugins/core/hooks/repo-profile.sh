#!/usr/bin/env bash
# repo-profile.sh — tells the session what this repo is before the first prompt, so the model picks the
# kit's matching skills instead of rescanning the code to find out.
# Trigger: SessionStart (startup|resume|clear|compact). Reads manifests and marker folders only — no model call:
# root, apps/*, packages/* package.json; pyproject.toml / requirements*.txt; go.mod, Cargo.toml; prisma/, drizzle/,
# alembic/, eas.json, .claude/docs/, docs/tickets/. Prints nothing for a folder with no manifest.
# An AI-assistant repo whose agent@harness is not on gets it enabled in .claude/settings.local.json (personal,
# excluded from git), effective next session. An explicit false in the project or local settings is never
# overridden. CLAUDE_REPO_PROFILE=0 turns the hook off. Never blocks: any failure exits 0.
[ "${CLAUDE_REPO_PROFILE:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 - <<'PY'
import glob, json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = r.stdout.strip() if r.returncode == 0 else cwd
except Exception:
    sys.exit(0)


def at(*parts):
    return os.path.join(top, *parts)


def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


deps, manifests = set(), []
for path in [at("package.json")] + sorted(glob.glob(at("apps", "*", "package.json")) +
                                          glob.glob(at("packages", "*", "package.json")))[:30]:
    pkg = load_json(path)
    if isinstance(pkg, dict):
        manifests.append("node")
        for key in ("dependencies", "devDependencies", "peerDependencies"):
            if isinstance(pkg.get(key), dict):
                deps.update(pkg[key])

py_text = ""
for path in [at("pyproject.toml")] + glob.glob(at("requirements*.txt")):
    try:
        py_text += open(path).read().lower() + "\n"
        manifests.append("python")
    except OSError:
        pass
for name, label in (("go.mod", "go"), ("Cargo.toml", "rust")):
    if os.path.exists(at(name)):
        manifests.append(label)
if not manifests:
    sys.exit(0)


def has_dep(*names):
    return any(n in deps for n in names)


def has_prefix(*prefixes):
    return any(d.startswith(p) for d in deps for p in prefixes)


def has_py(*names):
    return any(re.search(rf"(^|[\s\"'\[,]){re.escape(n)}([\s\"'\],<>=~!;\[]|$)", py_text, re.M) for n in names)


stack = []
mobile = has_dep("react-native", "expo") or os.path.exists(at("eas.json"))
web = has_dep("next") or (has_dep("react") and not mobile)
for cond, label in ((has_dep("next"), "Next.js"), (mobile, "React Native"), (web and not has_dep("next"), "React"),
                    (has_dep("@nestjs/core"), "NestJS"), (has_dep("express"), "Express"),
                    (has_dep("fastify"), "Fastify"), ("python" in manifests, "Python"),
                    (has_py("fastapi"), "FastAPI"), (has_py("django"), "Django"), (has_py("flask"), "Flask"),
                    ("go" in manifests, "Go"), ("rust" in manifests, "Rust"), (has_dep("typescript"), "TypeScript")):
    if cond:
        stack.append(label)
backend = any(s in stack for s in ("NestJS", "Express", "Fastify", "FastAPI", "Django", "Flask")) or has_dep("next")
ai = (has_prefix("@langchain/", "@copilotkit/", "@mastra/", "@ag-ui/")
      or has_py("langgraph", "langchain", "langchain-core", "copilotkit"))
db = [label for cond, label in ((has_dep("prisma", "@prisma/client") or os.path.isdir(at("prisma")), "Prisma"),
                                (has_dep("drizzle-orm") or os.path.isdir(at("drizzle")), "Drizzle"),
                                (has_py("alembic") or os.path.isdir(at("alembic")), "Alembic")) if cond]
has_docs = os.path.exists(at(".claude", "docs", "index.md"))


def enabled_at(path):
    s = load_json(path)
    if isinstance(s, dict) and isinstance(s.get("enabledPlugins"), dict):
        return s["enabledPlugins"].get("agent@harness")
    return None


local_path = at(".claude", "settings.local.json")
cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
agent_note = ""
if ai:
    local, project = enabled_at(local_path), enabled_at(at(".claude", "settings.json"))
    explicit = local if local is not None else project
    if explicit is None and enabled_at(os.path.join(cfg, "settings.json")) is not True:
        settings = {} if not os.path.exists(local_path) else load_json(local_path)
        if isinstance(settings, dict):
            try:
                settings.setdefault("enabledPlugins", {})["agent@harness"] = True
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, "w") as f:
                    json.dump(settings, f, indent=2)
                    f.write("\n")
                rel = ".claude/settings.local.json"
                if subprocess.run(["git", "-C", top, "check-ignore", "-q", rel]).returncode != 0:
                    ex = subprocess.run(["git", "-C", top, "rev-parse", "--git-path", "info/exclude"],
                                        capture_output=True, text=True).stdout.strip()
                    if ex:
                        ex = ex if os.path.isabs(ex) else os.path.join(top, ex)
                        os.makedirs(os.path.dirname(ex), exist_ok=True)
                        with open(ex, "a") as f:
                            f.write(rel + "\n")
                agent_note = ("Enabled agent@harness for this repo in .claude/settings.local.json — the /agent-* "
                              "skills load from the next session; say so if the user asks for agent work now.")
            except OSError:
                agent_note = ""

prefer = []
if ai:
    prefer.append("features → /agent-feature (not /feature), tools → /agent-tool, prove a turn → /agent-verify-turn")
if db:
    prefer.append("schema or queries → /db-change")
if backend and not ai:
    prefer.append("endpoints → /api-endpoint")
if web or mobile:
    prefer.append("UI → /ui-feature, from a Figma → /design-ui")
if mobile:
    prefer.append("releases → /release-checklist")
if os.path.isdir(at("docs", "tickets")):
    prefer.append("tracker work → /ticket <id>")

kind = ", ".join(stack + (["AI assistant"] if ai else []) + db) or "unrecognised stack"
lines = [f"REPO PROFILE: {kind}."]
if prefer:
    lines.append("Prefer: " + "; ".join(prefer) + " (CLAUDE.md and team plugins that cover this repo win).")
lines.append("Read .claude/docs/index.md before scanning source; /docs-sync before the PR." if has_docs
             else "No .claude/docs yet — /project-init builds it once, so later sessions skip the rescan.")
if agent_note:
    lines.append(agent_note)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}))
PY
exit 0
