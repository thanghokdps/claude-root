#!/usr/bin/env python3
"""lint-kit.py — structural checks for the kit's plugins. Exit 1 on any error; warnings don't fail.

Errors: SKILL.md frontmatter parses as YAML; no private names in agent (denylist); name == directory, kebab-case,
unique across plugins; description present, <=1024 chars, says when to use; only documented frontmatter keys; description + when_to_use
<=1536; ${CLAUDE_PLUGIN_ROOT}/ paths exist in the skill's own plugin and ${CLAUDE_SKILL_DIR}/ paths in its directory; hooks pass `bash -n` and are executable; inline python3 in a plugin .sh runs with -I; plugin/marketplace/hooks JSON parse; every plugin
is listed in the marketplace, dependencies exist and are acyclic; a SKILL.md body that names another plugin's skill
names a declared dependency or says "if (<plugin> is) installed"; every eval case loads its plugin and all its dependencies; same-named references/ files are identical across plugins; every file init.sh copies exists.
Warnings: SKILL.md over 500 lines; no trigger case under eval/triggers/.
"""
import filecmp
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(ROOT, "plugins")
errors, warnings = [], []
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TRIGGER = re.compile(r"\b(use (when|whenever|for|at|before|after|to)|run (at|when|after|before|once)|when to use)\b", re.I)


# Claude Code ignores unknown SKILL.md keys silently (docs: skills frontmatter reference, CLI 2.1.305).
SKILL_FIELDS = set("""name description when_to_use argument-hint arguments disable-model-invocation user-invocable
allowed-tools disallowed-tools model effort context agent background hooks paths shell metadata license compatibility""".split())
LISTING_CAP = 1536  # description + when_to_use are cut at this length in the skill listing


def unknown_fields(fm):
    return sorted(k for k in fm if k not in SKILL_FIELDS)


def listing_chars(fm):
    return len(str(fm.get("description") or "")) + len(str(fm.get("when_to_use") or ""))


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end]) or {}, text


def plugin_names():
    return sorted(d for d in os.listdir(PLUGINS_DIR) if os.path.isdir(os.path.join(PLUGINS_DIR, d, ".claude-plugin")))


def skill_paths():
    """(plugin, skill name, SKILL.md path) for every skill in every plugin."""
    for plugin in plugin_names():
        skills_dir = os.path.join(PLUGINS_DIR, plugin, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for name in sorted(os.listdir(skills_dir)):
            path = os.path.join(skills_dir, name, "SKILL.md")
            if os.path.isfile(path):
                yield plugin, name, path


def check_skills():
    names = {}
    for plugin, name, path in skill_paths():
        rel = os.path.relpath(path, ROOT)
        try:
            fm, text = frontmatter(path)
        except Exception as e:  # yaml.YAMLError, ValueError
            errors.append(f"{rel}: frontmatter does not parse — {str(e).splitlines()[0]}")
            continue
        if fm.get("name") != name:
            errors.append(f"{rel}: name '{fm.get('name')}' != directory '{name}'")
        if not KEBAB.match(name):
            errors.append(f"{rel}: directory name is not kebab-case")
        if name in names:
            errors.append(f"{rel}: duplicate skill name (also {names[name]})")
        names[name] = rel
        desc = fm.get("description") or ""
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f"{rel}: missing description")
        elif len(desc) > 1024:
            errors.append(f"{rel}: description is {len(desc)} chars (max 1024)")
        elif not TRIGGER.search(desc) and not fm.get("when_to_use"):
            errors.append(f"{rel}: description never says when to use it, and no when_to_use")
        for key in unknown_fields(fm):
            errors.append(f"{rel}: unknown frontmatter field '{key}' — Claude Code ignores it")
        if listing_chars(fm) > LISTING_CAP:
            errors.append(f"{rel}: description + when_to_use is {listing_chars(fm)} chars — the listing cuts at {LISTING_CAP}")
        wtu = fm.get("when_to_use")
        if wtu is not None and not isinstance(wtu, str):
            errors.append(f"{rel}: when_to_use is {type(wtu).__name__}, expected a string")
        # An installed plugin is copied on its own into the cache, so the root is the plugin, not the kit.
        for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+\w)", text):
            if not os.path.exists(os.path.join(PLUGINS_DIR, plugin, ref)):
                errors.append(f"{rel}: references missing file {ref} in plugins/{plugin}")
        for ref in re.findall(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+\w)", text):
            if not os.path.exists(os.path.join(os.path.dirname(path), ref)):
                errors.append(f"{rel}: references missing file {ref} in its skill directory")
        lines = text.count("\n")
        if lines > 500:
            warnings.append(f"{rel}: {lines} lines — loads in full on every invocation")
        if not os.path.isfile(os.path.join(ROOT, "eval", "triggers", f"{name}.json")):
            warnings.append(f"{rel}: no trigger case at eval/triggers/{name}.json")


def check_hooks():
    for plugin in plugin_names():
        for dirpath, _, files in os.walk(os.path.join(PLUGINS_DIR, plugin, "hooks")):
            for f in files:
                if not f.endswith(".sh"):
                    continue
                p = os.path.join(dirpath, f)
                rel = os.path.relpath(p, ROOT)
                if not os.access(p, os.X_OK):
                    errors.append(f"{rel}: not executable")
                r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
                if r.returncode:
                    errors.append(f"{rel}: bash -n failed — {r.stderr.strip().splitlines()[0]}")


UNISOLATED_PYTHON = re.compile(r"\bpython3?\s+-c?(?=\s|$)")


def unisolated_python(text):
    """Line numbers running inline python without -I: its cwd is the user's repo, whose json.py would load first."""
    return [n for n, line in enumerate(text.splitlines(), 1)
            if not line.lstrip().startswith("#") and UNISOLATED_PYTHON.search(line)]


def check_python_isolation():
    for dirpath, _, files in os.walk(PLUGINS_DIR):
        for f in files:
            if f.endswith(".sh"):
                p = os.path.join(dirpath, f)
                for n in unisolated_python(open(p).read()):
                    errors.append(f"{os.path.relpath(p, ROOT)}:{n}: inline python3 without -I")


def load_json(rel):
    try:
        return json.load(open(os.path.join(ROOT, rel)))
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"{rel}: invalid or missing JSON — {e}")
        return None


def check_json():
    for plugin in plugin_names():
        load_json(f"plugins/{plugin}/.claude-plugin/plugin.json")
        rel = f"plugins/{plugin}/hooks/hooks.json"
        if not os.path.exists(os.path.join(ROOT, rel)):
            continue
        data = load_json(rel) or {}
        for event in data.get("hooks", {}).values():
            for m in event:
                for h in m.get("hooks", []):
                    for script in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}\"?/([\w./-]+\.sh)", h.get("command", "")):
                        if not os.path.isfile(os.path.join(PLUGINS_DIR, plugin, script)):
                            errors.append(f"{rel}: hook script missing: {script}")


def find_cycle(graph):
    """First dependency cycle as a closed chain [a, b, a], or None."""
    state = {}

    def visit(node, chain):
        state[node] = "open"
        for dep in graph.get(node, []):
            if state.get(dep) == "open":
                return chain[chain.index(dep):] + [dep] if dep in chain else chain + [dep]
            if dep not in state:
                found = visit(dep, chain + [dep])
                if found:
                    return found
        state[node] = "done"
        return None

    for node in graph:
        if node not in state:
            found = visit(node, [node])
            if found:
                return found
    return None


def closure(graph, node):
    seen, todo = set(), list(graph.get(node, []))
    while todo:
        dep = todo.pop()
        if dep not in seen:
            seen.add(dep)
            todo.extend(graph.get(dep, []))
    return seen


SOFT_REF = re.compile(r"\bif (?:[\w-]+ is )?installed\b")


def undeclared_refs(lines, plugin, deps, owners):
    """(line number, skill) for each `/skill` owned by a plugin that is neither this one nor a dependency."""
    hits = []
    for i, line in enumerate(lines, 1):
        if SOFT_REF.search(line):
            continue
        for skill in re.findall(r"/([a-z0-9]+(?:-[a-z0-9]+)*)\b", line):
            owner = owners.get(skill)
            if owner and owner != plugin and owner not in deps and (i, skill) not in hits:
                hits.append((i, skill))
    return hits


def check_plugins():
    market = load_json(".claude-plugin/marketplace.json") or {}
    listed = {p["name"]: p.get("source", "") for p in market.get("plugins", [])}
    graph = {}
    for plugin in plugin_names():
        if listed.get(plugin) != f"./plugins/{plugin}":
            errors.append(f"plugins/{plugin}: not listed in marketplace.json with source ./plugins/{plugin}")
        manifest = load_json(f"plugins/{plugin}/.claude-plugin/plugin.json") or {}
        graph[plugin] = manifest.get("dependencies", [])
        for dep in graph[plugin]:
            if dep not in listed:
                errors.append(f"plugins/{plugin}: dependency '{dep}' is not in marketplace.json")
    cycle = find_cycle(graph)
    if cycle:
        errors.append(f"plugin dependency cycle: {' → '.join(cycle)}")
        return
    check_eval_cases(graph)
    owners = {name: plugin for plugin, name, _ in skill_paths()}
    for plugin, name, path in skill_paths():
        text = open(path, encoding="utf-8").read()
        head = text.count("\n", 0, text.index("\n---", 4) + 4)  # frontmatter: trigger phrases, not instructions
        body = text.splitlines()[head + 1:]
        for lineno, skill in undeclared_refs(body, plugin, closure(graph, plugin), owners):
            errors.append(f"{os.path.relpath(path, ROOT)}:{lineno + head + 1}: /{skill} is in {owners[skill]}, "
                          f"not a dependency of {plugin} — declare it or say \"if installed\" / \"if <plugin> is installed\"")


def missing_eval_plugins(declared, case_dir, needed):
    """Plugins in `needed` that the case's `plugins:` list does not load. `plugin eval` drops a plugin whose
    dependency is not loaded — the run goes on without it and every skill grader fails as a routing miss."""
    loaded = {os.path.basename(os.path.normpath(os.path.join(case_dir, d))) for d in declared or []}
    return sorted(set(needed) - loaded)


def check_eval_cases(graph):
    for plugin in graph:
        evals = os.path.join(PLUGINS_DIR, plugin, "evals")
        if not os.path.isdir(evals) or not graph[plugin]:
            continue
        for case in sorted(os.listdir(evals)):
            case_dir, prompt = os.path.join(evals, case), os.path.join(evals, case, "prompt.md")
            if not os.path.isfile(prompt):
                continue
            missing = missing_eval_plugins(frontmatter(prompt)[0].get("plugins"), case_dir,
                                           {plugin} | closure(graph, plugin))
            if missing:
                errors.append(f"{os.path.relpath(prompt, ROOT)}: plugins: does not load {', '.join(missing)} — "
                              f"list each as a path relative to the case (run via scripts/eval-plugin.sh)")


def missing_init_sources(script, core_dir):
    """Literal "$HARNESS_DIR/<path>" files init.sh copies that do not exist — its `cp … || true` hides them."""
    refs = re.findall(r'"\$HARNESS_DIR/([\w./-]+\.\w+)"', script)
    return sorted({r for r in refs if not os.path.exists(os.path.join(ROOT, core_dir, r))})


def check_init_sources():
    rel = "plugins/core/scripts/init.sh"
    for ref in missing_init_sources(open(os.path.join(ROOT, rel), encoding="utf-8").read(), "plugins/core"):
        errors.append(f"{rel}: copies missing file {ref}")


# Role packs share one shape so /feature can dispatch to any of them the same way; grows one pack per PR.
ROLE_PACKS = ("frontend", "backend", "ai")
ROLE_PACK_DEPS = ["progress", "dev"]


def role_pack_errors(plugin, agents, manifest, has_hooks):
    """Shape errors for one role pack: exactly one agents/<role>-engineer.md, the fixed dependencies, no hooks."""
    out = []
    if agents != [f"{plugin}-engineer.md"]:
        out.append(f"plugins/{plugin}: role pack must ship exactly agents/{plugin}-engineer.md, has {agents}")
    if manifest.get("dependencies") != ROLE_PACK_DEPS:
        out.append(f"plugins/{plugin}: role pack dependencies must be {ROLE_PACK_DEPS}, got {manifest.get('dependencies')}")
    if has_hooks:
        out.append(f"plugins/{plugin}: a role pack carries no hooks — a gate must run before the pack is enabled, so it lives in core/dev/ship")
    return out


def check_role_packs():
    for plugin in ROLE_PACKS:
        agents_dir = os.path.join(PLUGINS_DIR, plugin, "agents")
        agents = sorted(os.listdir(agents_dir)) if os.path.isdir(agents_dir) else []
        manifest = load_json(f"plugins/{plugin}/.claude-plugin/plugin.json") or {}
        errors.extend(role_pack_errors(plugin, agents, manifest, os.path.isdir(os.path.join(PLUGINS_DIR, plugin, "hooks"))))
    for plugin in plugin_names():
        if plugin not in ROLE_PACKS and os.path.isdir(os.path.join(PLUGINS_DIR, plugin, "rules", "stacks")):
            for f in os.listdir(os.path.join(PLUGINS_DIR, plugin, "rules", "stacks")):
                if f not in ("typescript.md", "javascript.md", "jest.md"):
                    errors.append(f"plugins/{plugin}/rules/stacks/{f}: framework rules belong to a role pack's rules/")


def check_shared_references():
    """A reference two plugins both need is copied (no cross-plugin paths in the cache); copies must not drift."""
    by_name = defaultdict(list)
    for plugin in plugin_names():
        ref_dir = os.path.join(PLUGINS_DIR, plugin, "references")
        if os.path.isdir(ref_dir):
            for f in os.listdir(ref_dir):
                by_name[f].append(os.path.join(ref_dir, f))
    for f, paths in by_name.items():
        for other in paths[1:]:
            if not filecmp.cmp(paths[0], other, shallow=False):
                errors.append(f"{os.path.relpath(other, ROOT)}: differs from {os.path.relpath(paths[0], ROOT)}")


# The kit repo is public, and agent and workplace skills/rules are distilled from private company code.
DENYLIST = re.compile(r"granbull|asoft-python|flash-agent|space-agent|on-behalf|space-v2|space-langchain"
                      r"|flash-mobile|space-api|space-chatbot", re.I)
DENYLIST_SCOPE = re.compile(r"^plugins/(ai|workplace)/")


def denylist_hits(text):
    return sorted({m.group(0).lower() for m in DENYLIST.finditer(text)})


def in_denylist_scope(rel):
    return bool(DENYLIST_SCOPE.match(rel))


def check_denylist():
    for dirpath, _, files in os.walk(PLUGINS_DIR):
        for f in files:
            rel = os.path.relpath(os.path.join(dirpath, f), ROOT)
            if not in_denylist_scope(rel):
                continue
            hits = denylist_hits(open(os.path.join(ROOT, rel), encoding="utf-8", errors="ignore").read())  # binary fixtures too
            if hits:
                errors.append(f"{rel}: private names in a public file — {', '.join(hits)}")


if __name__ == "__main__":
    check_skills()
    check_hooks()
    check_python_isolation()
    check_json()
    check_plugins()
    check_role_packs()
    check_shared_references()
    check_init_sources()
    check_denylist()
    for w in warnings:
        print(f"warn  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"lint-kit: {len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors else 0)
