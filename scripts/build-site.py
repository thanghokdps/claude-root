#!/usr/bin/env python3
"""build-site.py — copy the public docs into dist/ for the Vercel docs site.

Only the files in PUBLISHED reach dist/: the repo holds personal notes (PLAYBOOK.md) and
specs/ that must never be served. Paths keep their repo layout so relative links still resolve.
"""
import json
import shutil
import sys
from pathlib import Path

PUBLISHED = [
    "README.md",
    "DESIGN.md",
    "HARNESS.md",
    "docs/USAGE.md",
    "docs/skill-map.html",
    "docs/ddr/*.md",
    "eval/README.md",
    "plugins/README.md",
    "plugins/*/README.md",
]


def plugin_entries(root):
    entries = []
    for manifest in sorted(root.glob("plugins/*/.claude-plugin/plugin.json")):
        plugin_dir = manifest.parent.parent
        meta = json.loads(manifest.read_text())
        skills = sorted(p.parent.name for p in plugin_dir.glob("skills/*/SKILL.md"))
        entries.append({
            "name": meta["name"],
            "description": meta.get("description", ""),
            "dependencies": meta.get("dependencies", []),
            "skills": skills,
            "hooks": sorted(p.stem for p in plugin_dir.glob("hooks/*.sh")),
            "evals": len(list(plugin_dir.glob("evals/*/case.yaml"))),
            "readme": f"plugins/{plugin_dir.name}/README.md" if (plugin_dir / "README.md").exists() else None,
        })
    return entries


def build(root, out):
    if out.exists():
        shutil.rmtree(out)
    docs = []
    for pattern in PUBLISHED:
        for src in sorted(root.glob(pattern)):
            rel = src.relative_to(root).as_posix()
            dest = out / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            if rel.endswith(".md"):
                docs.append(rel)
    shutil.copy2(root / "site/index.html", out / "index.html")
    site = {
        "docs": docs,
        "plugins": plugin_entries(root),
        "triggers": len(list(root.glob("eval/triggers/*.json"))),
        "tests": len(list(root.glob("scripts/test_*.py"))),
    }
    (out / "site.json").write_text(json.dumps(site, indent=1))
    return site


if __name__ == "__main__":
    repo = Path(__file__).resolve().parent.parent
    site = build(repo, repo / "dist")
    print(f"dist/: {len(site['docs'])} docs, {len(site['plugins'])} plugins", file=sys.stderr)
