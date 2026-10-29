#!/usr/bin/env python3
"""Tests for build-site.py. Run: python3 scripts/test_build_site.py"""
import importlib.util
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build-site.py")
build_site = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_site)


def write(root, rel, text="x"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def fake_repo(d):
    root = Path(d) / "repo"
    for rel in ["README.md", "DESIGN.md", "HARNESS.md", "PLAYBOOK.md", "docs/USAGE.md",
                "docs/skill-map.html", "docs/ddr/0001-a.md", "specs/x/PLAN.md", "site/index.html",
                "plugins/README.md", "plugins/core/README.md", "plugins/core/skills/btw/SKILL.md",
                "plugins/core/skills/compact/SKILL.md", "plugins/core/rules/git.md"]:
        write(root, rel)
    write(root, "plugins/core/.claude-plugin/plugin.json",
          json.dumps({"name": "core", "description": "basics", "dependencies": ["progress"]}))
    return root


def test_only_published_files_reach_dist():
    with tempfile.TemporaryDirectory() as d:
        root, out = fake_repo(d), Path(d) / "dist"
        build_site.build(root, out)
        files = sorted(p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file())
        assert "PLAYBOOK.md" not in files and not any(f.startswith("specs/") for f in files), files
        assert "plugins/core/rules/git.md" not in files, files
        for rel in ["index.html", "site.json", "README.md", "docs/skill-map.html", "docs/ddr/0001-a.md",
                    "plugins/core/README.md"]:
            assert rel in files, (rel, files)


def test_site_json_lists_docs_and_plugins_with_skills():
    with tempfile.TemporaryDirectory() as d:
        root, out = fake_repo(d), Path(d) / "dist"
        build_site.build(root, out)
        site = json.loads((out / "site.json").read_text())
        assert "docs/USAGE.md" in site["docs"] and "docs/skill-map.html" not in site["docs"], site["docs"]
        assert site["plugins"] == [{"name": "core", "description": "basics", "dependencies": ["progress"],
                                    "skills": ["btw", "compact"], "readme": "plugins/core/README.md"}]


def test_rebuild_drops_stale_files():
    with tempfile.TemporaryDirectory() as d:
        root, out = fake_repo(d), Path(d) / "dist"
        write(out, "stale.md")
        build_site.build(root, out)
        assert not (out / "stale.md").exists()


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"ok {name}")
