#!/usr/bin/env bash
# repo-profile.sh — tells the session what this repo is before the first prompt, so the model picks the
# kit's matching skills instead of rescanning the code to find out.
# Trigger: SessionStart (startup|resume|clear|compact), and SubagentStart so subagents get the same profile (they
# never write settings). Reads manifests and marker folders only — no model call:
# root, apps/*, packages/* package.json; pyproject.toml / requirements*.txt; go.mod, Cargo.toml; prisma/, drizzle/,
# alembic/, eas.json, .claude/docs/, and specs/TICKETS.md in the repo's state dir (lib/state-dir.sh). A folder with no manifest gets only the role packs still off and how to enable one.
# Team setup: in a git repo (not $HOME) with no *@harness: false in its settings, SessionStart merges the kit
# marketplace, dev@harness and the packs below into .claude/settings.json, copies core's rules the repo and the
# user config both lack into .claude/rules/ (a plugin cannot ship always-loaded rules), and leaves both uncommitted.
# An opted-out repo gets the packs in .claude/settings.local.json (personal, excluded from git) instead.
# Packs, effective after /reload-plugins or a new session: frontend@harness for a web UI framework (not React Native alone),
# backend@harness for a server framework, a Worker, Firebase (firebase.json, firestore.rules, firebase-admin), an ORM, go, rust or an AI assistant, mobile@harness for react-native / expo / eas.json,
# devops@harness for a Worker, Dockerfile, compose file, CI workflow, *.tf, k8s/ or Chart.yaml, ai@harness for an AI
# assistant, workplace@harness for a
# `Domain: workplace` line in docs/requirements.md or .claude/docs/index.md, or two or more HR/workplace module
# folders (time off, booking, reservation, approval, maintenance, meal, lunch, attendance) under apps/,
# src/{modules,features}/ or apps/*/src/{api,modules}/. A `Domain: reverse-engineering` line in the same files only
# suggests reverse@harness: it ships an npx MCP server, so repo content never enables it. An explicit false in the project or local settings is never
# overridden. CLAUDE_REPO_PROFILE=0 turns the hook off. Never blocks: any failure exits 0.
[ "${CLAUDE_REPO_PROFILE:-1}" = "0" ] && exit 0
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

# -I: the cwd is an untrusted repo, so its json.py or PYTHON* env must never load into this hook.
HOOK_INPUT="$INPUT" RULES_DIR="$(dirname "${BASH_SOURCE[0]}")/../rules" \
  STATE_LIB="$(dirname "${BASH_SOURCE[0]}")/lib/state-dir.sh" python3 -I - <<'PY'
import glob, json, os, re, subprocess, sys

try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
    # SessionStart context never reaches a subagent, so SubagentStart repeats the profile; it never writes settings.
    event = "SubagentStart" if ev.get("hook_event_name") == "SubagentStart" else "SessionStart"
    cwd = ev.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    r = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    in_git = r.returncode == 0
    top = r.stdout.strip() if in_git else cwd
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


def is_kit():
    market = load_json(at(".claude-plugin", "marketplace.json"))
    return isinstance(market, dict) and market.get("name") == "harness"


def enabled_at(path, plugin):
    s = load_json(path)
    if isinstance(s, dict) and isinstance(s.get("enabledPlugins"), dict):
        return s["enabledPlugins"].get(plugin)
    return None


local_path = at(".claude", "settings.local.json")
shared_path = at(".claude", "settings.json")
cfg = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")


def kit_marketplace():
    """The public kit repo, never this machine's registration (that can be a personal SSH alias or a local path).
    Pinned to the tag of this core's version, so a push to the kit's main never reaches a team unreviewed; a repo
    moves to a newer kit by bumping `ref` in its own commit."""
    manifest = load_json(os.path.join(os.environ.get("RULES_DIR", ""), "..", ".claude-plugin", "plugin.json")) or {}
    source = {"source": "github", "repo": "thanghokdps/claude-root"}
    if isinstance(manifest.get("version"), str):
        source["ref"] = "v" + manifest["version"]
    return {"source": source}


def is_on(plugin):
    for path in (local_path, shared_path, os.path.join(cfg, "settings.json")):
        state = enabled_at(path, plugin)
        if state is not None:
            return state is True
    return False


def write_inside(path, text, append=False):
    """Write only a regular file whose folder resolves to where it claims; a cloned repo can plant symlinks."""
    folder = os.path.dirname(path)
    if os.path.islink(folder) or os.path.islink(path):
        raise OSError("symlink")
    os.makedirs(folder, exist_ok=True)
    if os.path.realpath(folder) != os.path.join(os.path.realpath(os.path.dirname(folder)), os.path.basename(folder)):
        raise OSError("folder resolves elsewhere")
    flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | (os.O_APPEND if append else os.O_TRUNC)
    with os.fdopen(os.open(path, flags, 0o600), "w") as f:
        f.write(text)


def opted_out():
    """Any *@harness: false in the repo's settings keeps the kit out of its team file (e.g. a client repo)."""
    for path in (local_path, shared_path):
        s = load_json(path)
        plugins = s.get("enabledPlugins") if isinstance(s, dict) else None
        if isinstance(plugins, dict) and any(k.endswith("@harness") and v is False for k, v in plugins.items()):
            return True
    return False


def setup_repo(plugins):
    """Add the kit marketplace, dev and the repo's packs to .claude/settings.json so teammates get them once it is
    committed. Returns what it added ([] when already there), or None when the repo is not set up this way."""
    if event != "SessionStart" or not in_git or opted_out():
        return None
    if os.path.realpath(top) == os.path.realpath(os.path.expanduser("~")):
        return None
    # The kit is the harness marketplace itself: team setup here only leaves an untracked settings.json each session.
    if is_kit():
        return None
    if os.path.islink(at(".claude")) or os.path.islink(shared_path):
        return None
    settings = load_json(shared_path) if os.path.exists(shared_path) else {}
    if not isinstance(settings, dict):
        return None
    markets, enabled = settings.get("extraKnownMarketplaces", {}), settings.get("enabledPlugins", {})
    if not isinstance(markets, dict) or not isinstance(enabled, dict):
        return None
    added = []
    if "harness" not in markets:
        settings.setdefault("extraKnownMarketplaces", {})["harness"] = kit_marketplace()
        added.append("the harness marketplace")
    for plugin in ["dev@harness"] + plugins:
        if plugin not in enabled:
            settings.setdefault("enabledPlugins", {})[plugin] = True
            added.append(plugin)
    if added:
        try:
            write_inside(shared_path, json.dumps(settings, indent=2) + "\n")
        except OSError:
            return None
    copy_rules()
    return added


copied_rules = []


def copy_rules():
    """Copy each core rule that neither .claude/rules/ nor the user config has; a same-named team rule wins.
    shortcut: a copied rule never refreshes when the kit changes it; delete the file to get the new one."""
    src = os.environ.get("RULES_DIR", "")
    for path in sorted(glob.glob(os.path.join(src, "*.md"))):
        name = os.path.basename(path)
        dest = at(".claude", "rules", name)
        if os.path.lexists(dest) or os.path.exists(os.path.join(cfg, "rules", name)):
            continue
        try:
            write_inside(dest, open(path).read())
        except OSError:
            return
        copied_rules.append(name)


def setup_note(added):
    wrote = ([f".claude/settings.json ({', '.join(added)})"] if added else []) + (
        [f"{len(copied_rules)} core rule{'s' if len(copied_rules) > 1 else ''} into .claude/rules/"]
        if copied_rules else [])
    return (f"Wrote {' and '.join(wrote)}, uncommitted: tell the user in your first reply that committing them "
            "gives teammates the kit and its rules when they trust the folder, or that they can remove them; "
            "plugins it turns on load after /reload-plugins.") if wrote else ""


def blocked_reads():
    """(context line, user note) when a settings file makes the file tools refuse the kit's own rule files."""
    for path in (local_path, shared_path, os.path.join(cfg, "settings.json")):
        perms = (load_json(path) if os.path.exists(path) else None) or {}
        perms = perms.get("permissions") if isinstance(perms, dict) else None
        if isinstance(perms, dict) and perms.get("blockReadsOutsideWorkingDirectories") is True:
            # Answering 2 to auto mode's first-read prompt writes this key; every skill then loses its rules.
            fix = (f"remove permissions.blockReadsOutsideWorkingDirectories from {path} and restart, or type "
                   f"/add-dir {os.path.join(cfg, 'plugins')} for this session")
            return ("REPO PROFILE: the file tools refuse reads outside the working directories, so the kit's skills "
                    f"cannot read their rules under {os.path.join(cfg, 'plugins')}. Before any skill, tell the user "
                    f"to {fix}.",
                    f"Harness skills cannot read their rules: {fix}.")
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
if is_kit():
    # The kit's own CI workflow made it a devops repo and enabled devops@harness in its local settings.
    lines = ["REPO PROFILE: the harness kit itself — no role packs. Follow its CLAUDE.md; the gate is "
             "`bash scripts/check.sh`."]
    blocked = blocked_reads()
    if blocked:
        lines.append(blocked[0])
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(lines)}}))
    sys.exit(0)
if not manifests:
    # Nothing to detect from yet, and a pack enabled now loads only after a reload: say so before a stack is scaffolded.
    # ai depends on frontend and backend; install.sh turns them off at user scope, and a dependency disabled anywhere
    # disables ai too, so the team file must turn them on wherever ai is.
    companions = ([p for p in ("frontend@harness", "backend@harness") if not is_on(p)]
                  if is_on("ai@harness") else [])
    added = setup_repo(companions)
    off = [p for p in ("frontend@harness", "backend@harness", "mobile@harness", "devops@harness", "ai@harness")
           if not is_on(p)]
    # .claude/settings.json is a guarded path (sensitive-path), so the CLI enables the pack, never an Edit by the model.
    enable = ("ask the user to run `claude plugin enable <pack> --scope project`" if added is not None
              else "ask the user to run `claude plugin enable <pack> --scope local`")
    lines = []
    if off:
        ai_hint = "ai@harness for LangChain / LangGraph / Mastra / CopilotKit / Langfuse, " if "ai@harness" in off else ""
        lines.append("REPO PROFILE: new repo, no manifest yet. Role packs off here: " + ", ".join(off) + ". Before "
                     f"scaffolding a stack, stop and tell the user which pack it needs ({ai_hint}frontend, backend, "
                     f"mobile, devops by stack), {enable}, and ask them to type /reload-plugins (or start a new "
                     "session) so its skills load.")
    if is_on("ai@harness"):
        # A session once hand-wrote an API-only chatbot here with ai on: the hint never named the skill that was loaded.
        lines.append("REPO PROFILE: new repo, ai@harness is on. Any request to init, set up or scaffold a chatbot or AI "
                     "assistant (LangChain, LangGraph, Mastra, CopilotKit, Langfuse; with or without features) goes "
                     "through /agent-architect first; it builds a chat page that streams a real reply. Never "
                     "hand-write the scaffold. Any other assistant request goes through its skill even with no code "
                     "yet: a feature → /agent-feature, a write behind a confirm card → /agent-hitl, documents or a "
                     "vector store → /agent-rag, a tool → /agent-tool, routing → /agent-graph. Invoke the skill "
                     "before asking questions or planning; never plan or build the layer by hand.")
    user_note = ""
    if companions:
        # Asked mid-scaffold, a missing pack cost the user a stop and a reload; ask before anything starts.
        names = " and ".join(companions)
        if added is not None:
            step = "type /reload-plugins (or start a new session)"
            done = f"{names} {'are' if len(companions) > 1 else 'is'} now enabled in .claude/settings.json but not loaded"
        else:
            cmds = [f"`claude plugin enable {p} --scope local`" for p in companions]
            step = f"run {' and '.join(cmds)}, then type /reload-plugins"
            done = f"{names} {'are' if len(companions) > 1 else 'is'} off"
        lines.append(f"REPO PROFILE: ai@harness is on and {done}; ai depends on them and does not load without them. "
                     f"In your first reply, before any skill, preflight or plan, ask the user to {step}.")
        user_note = (f"New repo with ai@harness: the assistant needs {names}. Before asking for a scaffold, "
                     f"{step.replace('`claude', '`! claude')}.")
    if setup_note(added or []):
        lines.append(setup_note(added or []))
    blocked = blocked_reads()
    if blocked:
        lines.append(blocked[0])
        user_note = " ".join(filter(None, (blocked[1], user_note)))
    if lines:
        out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(lines)}}
        if user_note and event == "SessionStart":
            out["systemMessage"] = user_note
        print(json.dumps(out))
    sys.exit(0)


def has_dep(*names):
    return any(n in deps for n in names)


def has_prefix(*prefixes):
    return any(d.startswith(p) for d in deps for p in prefixes)


def has_py(*names):
    return any(re.search(rf"(^|[\s\"'\[,]){re.escape(n)}([\s\"'\],<>=~!;\[]|$)", py_text, re.M) for n in names)


stack = []
mobile = has_dep("react-native", "expo") or os.path.exists(at("eas.json"))
react = has_dep("react") and not mobile and not has_dep("next")
web_labels = [label for cond, label in ((has_dep("next"), "Next.js"), (react, "React"), (has_dep("nuxt"), "Nuxt"),
                                        (has_dep("vue") and not has_dep("nuxt"), "Vue"),
                                        (has_dep("@sveltejs/kit"), "SvelteKit"), (has_dep("astro"), "Astro")) if cond]
web = bool(web_labels)
backends = [label for cond, label in ((has_dep("@nestjs/core"), "NestJS"), (has_dep("express"), "Express"),
                                      (has_dep("fastify"), "Fastify"), (has_dep("hono"), "Hono"),
                                      (has_dep("koa"), "Koa"), (has_dep("elysia"), "Elysia"),
                                      (has_py("fastapi"), "FastAPI"), (has_py("django"), "Django"),
                                      (has_py("flask"), "Flask")) if cond]
workers = has_dep("wrangler") or any(os.path.exists(at(f"wrangler.{ext}")) for ext in ("toml", "jsonc", "json"))
# The client `firebase` SDK alone is a frontend dependency; project config, rules or the Admin SDK mean server-side data.
firebase = (has_dep("firebase-admin") or os.path.exists(at("firebase.json")) or os.path.exists(at("firestore.rules")))
for cond, label in ((True, web_labels), (mobile, ["React Native"]), ("python" in manifests, ["Python"]),
                    (True, backends), (workers, ["Cloudflare Workers"]), (firebase, ["Firebase"]),
                    ("go" in manifests, ["Go"]), ("rust" in manifests, ["Rust"]),
                    (has_dep("typescript"), ["TypeScript"])):
    if cond:
        stack.extend(label)
# A Worker is a server and its wrangler config is deploy config, so it brings backend and devops.
backend = bool(backends) or has_dep("next") or workers or firebase
ai = (has_prefix("@langchain/", "@copilotkit/", "@mastra/", "@ag-ui/")
      or has_py("langgraph", "langchain", "langchain-core", "copilotkit"))
db = [label for cond, label in ((has_dep("prisma", "@prisma/client") or os.path.isdir(at("prisma")), "Prisma"),
                                (has_dep("drizzle-orm") or os.path.isdir(at("drizzle")), "Drizzle"),
                                (has_py("alembic") or os.path.isdir(at("alembic")), "Alembic")) if cond]
has_docs = os.path.exists(at(".claude", "docs", "index.md"))


def domain_marked(name):
    for path in (at("docs", "requirements.md"), at(".claude", "docs", "index.md")):
        try:
            if re.search(rf"(?im)^[\s*>-]*Domain\**\s*:\**\s*`?{name}\b", open(path).read()):
                return True
        except OSError:
            pass
    return False


modules = [os.path.basename(p).lower() for parent in ("apps", "src/modules", "src/features", "apps/*/src/api",
                                                     "apps/*/src/modules")
           for p in glob.glob(at(parent, "*"))[:200] if os.path.isdir(p)]
workplace = domain_marked("workplace") or sum(1 for m in modules if re.search(
    r"time-?off|leave|booking|reservation|approval|maintenance|meal|lunch|attendance", m)) >= 2
# Suggested, never enabled: the pack starts an npx MCP server, and a cloned repo's text and .npmrc must not be able to
# switch that on. Only the marker line counts.
reverse = domain_marked("reverse-engineering")
# Role and domain packs stay off at user scope (install.sh) and are turned on here for the repos that need them.
# ai depends on frontend and backend, so an AI repo turns both on even with no web UI.
frontend = web or ai
# An AI repo runs an agent server even with no web framework or ORM (LangGraph's own server, Mastra).
backend_pack = backend or bool(db) or "go" in manifests or "rust" in manifests or ai
devops = workers or bool(glob.glob(at("Dockerfile*")) or glob.glob(at("docker-compose*")) or glob.glob(at("compose.y*ml"))
             or glob.glob(at(".github", "workflows", "*.y*ml")) or os.path.exists(at(".gitlab-ci.yml"))
             or glob.glob(at("*.tf")) or glob.glob(at("*", "*.tf")) or os.path.isdir(at("k8s"))
             or glob.glob(at("*", "Chart.yaml")) or os.path.exists(at("Chart.yaml")))
roles = [r for r, on in (("frontend", frontend), ("backend", backend_pack), ("mobile", mobile), ("devops", devops),
                         ("ai", ai)) if on]
packs = [p for p, on in (("frontend@harness", frontend), ("backend@harness", backend_pack), ("mobile@harness", mobile),
                         ("devops@harness", devops), ("ai@harness", ai), ("workplace@harness", workplace)) if on]


added = setup_repo(packs)
to_enable = []
for plugin in packs if added is None else []:
    local, project = enabled_at(local_path, plugin), enabled_at(at(".claude", "settings.json"), plugin)
    explicit = local if local is not None else project
    if explicit is None and enabled_at(os.path.join(cfg, "settings.json"), plugin) is not True:
        to_enable.append(plugin)
enable_note = ""
# The AI pack was named agent@harness before 2026-10-30; a local file still enabling it is rewritten to ai@harness.
legacy = enabled_at(local_path, "agent@harness") is not None
if (to_enable or legacy) and event == "SessionStart":
    claude_dir = at(".claude")
    if os.path.islink(claude_dir) or os.path.islink(local_path):
        settings = None
    else:
        settings = {} if not os.path.exists(local_path) else load_json(local_path)
    if isinstance(settings, dict):
        try:
            if legacy:
                settings["enabledPlugins"]["ai@harness"] = settings["enabledPlugins"].pop("agent@harness")
            for plugin in to_enable:
                settings.setdefault("enabledPlugins", {})[plugin] = True
            write_inside(local_path, json.dumps(settings, indent=2) + "\n")
            rel = ".claude/settings.local.json"
            if subprocess.run(["git", "-C", top, "check-ignore", "-q", rel]).returncode != 0:
                ex = subprocess.run(["git", "-C", top, "rev-parse", "--git-path", "info/exclude"],
                                    capture_output=True, text=True).stdout.strip()
                if ex:
                    ex = ex if os.path.isabs(ex) else os.path.join(top, ex)
                    try:
                        write_inside(ex, rel + "\n", append=True)
                    except OSError:
                        pass
            enable_note = (f"Enabled {', '.join(to_enable)} for this repo in .claude/settings.local.json — their "
                           "skills load from the next session; say so if the user asks for that work now.")
        except OSError:
            enable_note = ""

prefer = ["features across roles → /feature, which dispatches each slice to its pack's engineer"]
if ai:
    prefer.append("agent tools → /agent-tool, HITL → /agent-hitl, prove a turn → /agent-verify-turn")
if db:
    prefer.append("schema or queries → /db-change")
if backend_pack:
    prefer.append("endpoints → /api-endpoint")
if workers:
    prefer.append("Worker code → backend's rules/cloudflare-workers.md, first deploy → /release-setup cloudflare")
if firebase:
    prefer.append("Firestore → backend's rules/firestore.md, sign-in → rules/firebase-auth.md, push → rules/fcm.md")
if web:
    prefer.append("UI → /ui-feature, from a Figma → /design-ui")
if mobile:
    prefer.append("screens → /mobile-feature, releases → /release-checklist")
if devops:
    prefer.append("CI → /pipeline, images → /container, terraform / k8s / helm → /infra-change")
state = subprocess.run(["bash", "-c", '. "$1" && state_dir "$2"', "_", os.environ["STATE_LIB"], top],
                       capture_output=True, text=True).stdout.strip() if in_git else ""
if state and os.path.exists(os.path.join(state, "specs", "TICKETS.md")):  # /breakdown and /ticket write it
    prefer.append("tracker work → /ticket <id>")

kind = ", ".join(stack + (["AI assistant"] if ai else []) + db) or "unrecognised stack"
lines = [f"REPO PROFILE: {kind}."]
if roles:
    lines.append("Roles: " + ", ".join(roles) + ".")
if prefer:
    lines.append("Prefer: " + "; ".join(prefer) + " (CLAUDE.md and team plugins that cover this repo win).")
lines.append("Read .claude/docs/index.md before scanning source; /docs-sync before the PR." if has_docs
             else "No .claude/docs yet — /project-init builds it once, so later sessions skip the rescan.")
if workplace:
    lines.append("Domain: workplace — requests, approvals, balances or bookings → /workplace-review before the PR.")
if reverse:
    lines.append("Domain: reverse-engineering — shipped apps, binaries, APKs or firmware → /reverse-engineer-anything "
                 "(reverse@harness, off by default: if the skill is missing, tell the user to run "
                 "`claude plugin enable reverse@harness --scope local` and open a new session).")
for note in (enable_note, setup_note(added or [])):
    if note:
        lines.append(note)
blocked = blocked_reads()
if blocked:
    lines.append(blocked[0])
out = {"hookSpecificOutput": {"hookEventName": event, "additionalContext": "\n".join(lines)}}
if blocked and event == "SessionStart":
    out["systemMessage"] = blocked[1]
print(json.dumps(out))
PY
exit 0
