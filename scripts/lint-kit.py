#!/usr/bin/env python3
"""lint-kit.py — structural checks for the kit. Exit 1 on any error; warnings don't fail.

Errors: SKILL.md frontmatter parses as YAML; name == directory, kebab-case, unique;
description present, <=1024 chars, says when to use; ${CLAUDE_PLUGIN_ROOT}/ paths exist;
hooks pass `bash -n` and are executable; plugin/marketplace/hooks JSON parse.
Warnings: SKILL.md over 500 lines; no trigger case under eval/triggers/.
"""
import json
import os
import re
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, warnings = [], []
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TRIGGER = re.compile(r"\b(use (when|whenever|for|at|before|after|to)|run (at|when|after|before|once)|when to use)\b", re.I)


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---\n"):
        raise ValueError("no frontmatter")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end]) or {}, text


def check_skills():
    names = {}
    skills_dir = os.path.join(ROOT, "skills")
    for name in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, name, "SKILL.md")
        if not os.path.isfile(path):
            continue
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
        wtu = fm.get("when_to_use")
        if wtu is not None and not isinstance(wtu, str):
            errors.append(f"{rel}: when_to_use is {type(wtu).__name__}, expected a string")
        for ref in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+\w)", text):
            if not os.path.exists(os.path.join(ROOT, ref)):
                errors.append(f"{rel}: references missing file {ref}")
        lines = text.count("\n")
        if lines > 500:
            warnings.append(f"{rel}: {lines} lines — loads in full on every invocation")
        if not os.path.isfile(os.path.join(ROOT, "eval", "triggers", f"{name}.json")):
            warnings.append(f"{rel}: no trigger case at eval/triggers/{name}.json")


def check_hooks():
    hooks_dir = os.path.join(ROOT, "hooks")
    for dirpath, _, files in os.walk(hooks_dir):
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


def check_json():
    for rel in [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "hooks/hooks.json"]:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        try:
            data = json.load(open(p))
        except json.JSONDecodeError as e:
            errors.append(f"{rel}: invalid JSON — {e}")
            continue
        if rel == "hooks/hooks.json":
            for event in data.get("hooks", {}).values():
                for m in event:
                    for h in m.get("hooks", []):
                        for script in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}\"?/([\w./-]+\.sh)", h.get("command", "")):
                            if not os.path.isfile(os.path.join(ROOT, script)):
                                errors.append(f"{rel}: hook script missing: {script}")


check_skills()
check_hooks()
check_json()
for w in warnings:
    print(f"warn  {w}")
for e in errors:
    print(f"ERROR {e}")
print(f"lint-kit: {len(errors)} error(s), {len(warnings)} warning(s)")
sys.exit(1 if errors else 0)
