#!/usr/bin/env python3
"""Build the drill-down map model of this kit for super-board's /visual skill.

  python3 scripts/skill-map.py > map.json
  python3 scripts/skill-map.py --plugin ai > map.json      # one plugin and its dependencies only
  python3 <super-board>/skills/visual/scripts/visual.py render --map map.json --out docs/skill-map.html

Nodes come from plugin.json, SKILL.md frontmatter and hook headers, so the map follows the kit; the two
workflow views are curated below because their order is a design decision, not something to infer.
"""
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS = os.path.join(ROOT, "plugins")
ORDER = ["progress", "core", "plan", "review", "dev", "ship", "frontend", "backend", "mobile", "devops", "ai", "lead", "guards"]
ROLE = {
    "progress": "live ✅ checklist", "core": "session + project basics", "plan": "design before code",
    "review": "diffs, PRs, impact", "dev": "build, fix, test-first", "ship": "release + CI",
    "frontend": "role pack: web UI", "backend": "role pack: server side", "mobile": "role pack: React Native",
    "devops": "role pack: CI, containers, infra", "ai": "role pack: AI assistants",
    "lead": "retro, skill authoring", "guards": "opt-in hooks",
}


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def first_sentence(s):
    return re.split(r"(?<=[.!?])\s|\s—\s", s.strip(), maxsplit=1)[0].rstrip(".")


def skill_node(plugin, name):
    rel = f"plugins/{plugin}/skills/{name}/SKILL.md"
    text = read(os.path.join(ROOT, rel))
    fm = yaml.safe_load(re.match(r"---\n(.*?)\n---", text, re.S).group(1))
    desc = fm.get("description") or ""
    use = re.search(r"Use (?:this )?(?:when|whenever|for|before)\b.*", desc)
    when = str(fm.get("when_to_use") or (use.group(0) if use else "On request."))
    invoke = re.search(r"\*\*Invoke:\*\*\s*(.+)", text)
    done = re.search(r"\*\*Done when:\*\*\s*(.+)", text)
    how = []
    if invoke:
        how.append(f"Run {invoke.group(1).strip()}.")
    how.append(desc)
    if done:
        how.append(f"Done when {done.group(1).strip()}")
    return {"id": name, "label": f"/{name}", "kind": "public", "what": first_sentence(desc),
            "when": when, "how": " ".join(how), "source": rel, "sublabel": plugin}, text


def hook_nodes(plugin):
    path = os.path.join(PLUGINS, plugin, "hooks", "hooks.json")
    if not os.path.exists(path):
        return []
    events = {}  # one script can be registered on several events
    for event, matchers in json.load(open(path))["hooks"].items():
        for m in matchers:
            for h in m["hooks"]:
                events.setdefault(h["command"].split("/")[-1].strip('"'), []).append(event)
    nodes = []
    for script, evs in events.items():
        rel = f"plugins/{plugin}/hooks/{script}"
        header = [l.lstrip("# ").strip() for l in read(os.path.join(ROOT, rel)).splitlines()[1:6]
                  if l.startswith("#") and l.strip("# ")]
        what = re.sub(rf"^{re.escape(script)}\s*[—:-]\s*", "", header[0]) if header else script
        nodes.append({"id": f"h-{script[:-3]}", "label": script[:-3], "kind": "hook",
                      "sublabel": ", ".join(dict.fromkeys(evs)), "what": what,
                      "when": f"Fires on {', '.join(dict.fromkeys(evs))}.",
                      "how": " ".join(header) or what, "source": rel})
    return nodes


def closure(name):
    """`name` and every plugin it depends on, in kit order."""
    seen, todo = set(), [name]
    while todo:
        p = todo.pop()
        if p not in seen:
            seen.add(p)
            todo += json.load(open(os.path.join(PLUGINS, p, ".claude-plugin", "plugin.json"))).get("dependencies", [])
    return [p for p in ORDER if p in seen]


def main():
    only = sys.argv[sys.argv.index("--plugin") + 1] if "--plugin" in sys.argv else None
    order = closure(only) if only else ORDER
    nodes, edges, views, skills, texts = [], [], [], {}, {}
    for p in order:
        meta = json.load(open(os.path.join(PLUGINS, p, ".claude-plugin", "plugin.json")))
        nodes.append({"id": f"p-{p}", "label": p, "kind": "lane", "sublabel": ROLE[p],
                      "what": meta["description"], "when": f"/plugin install {p}@harness, or via the harness bundle.",
                      "how": f"Version {meta['version']}. Depends on: {', '.join(meta.get('dependencies', [])) or 'nothing'}.",
                      "source": f"plugins/{p}/.claude-plugin/plugin.json"})
        for dep in meta.get("dependencies", []):
            edges.append({"id": f"dep-{p}-{dep}", "from": f"p-{p}", "to": f"p-{dep}", "label": "depends on"})
        skill_dir = os.path.join(PLUGINS, p, "skills")
        names = sorted(os.listdir(skill_dir)) if os.path.isdir(skill_dir) else []
        for n in names:
            node, text = skill_node(p, n)
            nodes.append(node)
            skills[n], texts[n] = p, text
        hooks = hook_nodes(p)
        nodes += hooks
        views.append({"id": f"p-{p}", "parent": "overview", "title": p, "caption": ROLE[p],
                      "nodeIds": names + [h["id"] for h in hooks]})

    # Hand-offs: a skill that names another skill of the same plugin as `/name` hands work to it.
    for src, text in texts.items():
        for dst in sorted(set(re.findall(r"(?<![\w/.-])/([a-z][a-z-]+)\b", text))):
            if dst != src and skills.get(dst) == skills[src]:
                edges.append({"id": f"h-{src}-{dst}", "from": src, "to": dst, "label": "hands off"})

    if only:
        return emit_single(only, order, nodes, edges, views)
    nodes.append({"id": "harness", "label": "harness", "kind": "board", "sublabel": "bundle — install this",
                  "what": "The one install: depends on all nine role plugins.",
                  "when": "/plugin install harness@harness, or bash scripts/install.sh from a clone.",
                  "how": "Each role plugin can also be installed alone; its dependencies come with it.",
                  "source": "plugins/harness/.claude-plugin/plugin.json"})
    for p in ORDER:
        if not any(e["to"] == f"p-{p}" for e in edges if e["id"].startswith("dep-")) or p in ("guards", "frontend", "backend", "mobile", "devops", "ai"):
            edges.append({"id": f"dep-harness-{p}", "from": "harness", "to": f"p-{p}", "label": "installs"})

    start = ["brainstorming", "writing-plans", "project-init", "feature", "review-checklist", "finish-branch"]
    agent = ["agent-architect", "agent-feature", "agent-tool", "agent-hitl", "agent-frontend",
             "agent-verify-turn", "agent-evals", "agent-security"]
    chain = lambda ids, label: [{"id": f"w-{a}-{b}", "from": a, "to": b, "label": label} for a, b in zip(ids, ids[1:])]
    views += [
        {"id": "start", "parent": "overview", "title": "Start a project",
         "caption": "Empty folder: design → plan → scaffold, then /project-init. Existing repo: start at /project-init.",
         "nodeIds": start, "mainSteps": True, "edges": chain(start, "then")},
        {"id": "ai-assistant", "parent": "overview", "title": "Build an AI assistant",
         "caption": "CopilotKit + AG-UI + LangGraph: one skill per layer, proven by a real turn and evals.",
         "nodeIds": agent, "edges": [
             {"id": "a1", "from": "agent-architect", "to": "agent-feature", "label": "ADR + scaffold"},
             {"id": "a2", "from": "agent-feature", "to": "agent-tool", "label": "tool slice"},
             {"id": "a3", "from": "agent-feature", "to": "agent-hitl", "label": "write slice"},
             {"id": "a4", "from": "agent-feature", "to": "agent-frontend", "label": "UI slice"},
             {"id": "a5", "from": "agent-tool", "to": "agent-verify-turn", "label": "prove"},
             {"id": "a6", "from": "agent-hitl", "to": "agent-verify-turn", "label": "prove"},
             {"id": "a7", "from": "agent-frontend", "to": "agent-verify-turn", "label": "prove"},
             {"id": "a8", "from": "agent-verify-turn", "to": "agent-evals", "label": "lock in"},
             {"id": "a9", "from": "agent-evals", "to": "agent-security", "label": "before ship"}]},
    ]
    views.insert(0, {"id": "overview", "parent": None, "title": "harness",
                     "caption": "One install, nine role plugins. Double-click a plugin to see its skills.",
                     "nodeIds": ["harness"] + [f"p-{p}" for p in ORDER]})
    json.dump({"title": "harness — skill map", "root": "overview", "nodes": nodes, "edges": edges,
               "views": views, "browserOrder": ["start", "ai-assistant"] + [f"p-{p}" for p in ORDER]},
              sys.stdout, indent=1, ensure_ascii=False)


def emit_single(only, order, nodes, edges, views):
    agent = ["agent-architect", "agent-feature", "agent-tool", "agent-hitl", "agent-frontend",
             "agent-verify-turn", "agent-evals", "agent-security"]
    land = ["agent-feature", "verify-done", "review-checklist", "finish-branch"]
    ids = {n["id"] for n in nodes}
    chain = lambda xs, label: [{"id": f"w-{a}-{b}", "from": a, "to": b, "label": label} for a, b in zip(xs, xs[1:])]
    if only == "ai" and set(agent + land) <= ids:
        views += [
            {"id": "ai-assistant", "parent": "overview", "title": "Build an AI assistant",
             "caption": "One skill per layer, proven by a real turn and evals.",
             "nodeIds": agent, "edges": [
                 {"id": "a1", "from": "agent-architect", "to": "agent-feature", "label": "ADR + scaffold"},
                 {"id": "a2", "from": "agent-feature", "to": "agent-tool", "label": "tool slice"},
                 {"id": "a3", "from": "agent-feature", "to": "agent-hitl", "label": "write slice"},
                 {"id": "a4", "from": "agent-feature", "to": "agent-frontend", "label": "UI slice"},
                 {"id": "a5", "from": "agent-tool", "to": "agent-verify-turn", "label": "prove"},
                 {"id": "a6", "from": "agent-hitl", "to": "agent-verify-turn", "label": "prove"},
                 {"id": "a7", "from": "agent-frontend", "to": "agent-verify-turn", "label": "prove"},
                 {"id": "a8", "from": "agent-verify-turn", "to": "agent-evals", "label": "lock in"},
                 {"id": "a9", "from": "agent-evals", "to": "agent-security", "label": "before ship"}]},
            {"id": "land", "parent": "overview", "title": "Review and land a feature",
             "caption": "agent-feature Step 8 hands off to the dependency plugins.",
             "nodeIds": land, "mainSteps": True, "edges": chain(land, "then")},
        ]
    views.insert(0, {"id": "overview", "parent": None, "title": only,
                     "caption": f"{only} and the plugins it installs with it. Double-click a plugin to see its skills.",
                     "nodeIds": [f"p-{p}" for p in order]})
    json.dump({"title": f"{only} — skill map", "root": "overview", "nodes": nodes, "edges": edges, "views": views,
               "browserOrder": [v["id"] for v in views if v["id"] in ("ai-assistant", "land")] + [f"p-{p}" for p in order]},
              sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
