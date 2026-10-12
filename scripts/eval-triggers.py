#!/usr/bin/env python3
"""eval-triggers.py — deterministic routing check for the kit's skill descriptions (no model calls).

Each eval/triggers/<skill>.json holds prompts that should rank the skill in its top_k
(positive) and prompts owned by another skill that must not rank it first (negative).
Scoring is stemmed TF-IDF cosine over name + description + when_to_use: a lexical proxy
for the real router. A failure usually means fix the description, not the case.
Also flags description pairs that nearly collide.

Usage: scripts/eval-triggers.py [--collide 0.45] [skill ...]
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOP = set("""a an the and or of to in on for with without from by at is are be this that it its
your you my me i we our as into not no do does when what how why should use used using can any
all each every before after then than if else so just""".split())


def stem(w):
    for suf in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def tokens(text):
    return [stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


def load_skills():
    skills = {}
    for name in sorted(os.listdir(os.path.join(ROOT, "skills"))):
        p = os.path.join(ROOT, "skills", name, "SKILL.md")
        if not os.path.isfile(p):
            continue
        text = open(p, encoding="utf-8").read()
        fm = yaml.safe_load(text[4:text.index("\n---", 4)]) or {}
        doc = " ".join([name.replace("-", " ")] * 2 + [fm.get("description", ""), str(fm.get("when_to_use", ""))])
        skills[name] = tokens(doc)
    return skills


def build_index(skills):
    df = Counter(t for toks in skills.values() for t in set(toks))
    n = len(skills)
    idf = {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}
    vecs = {}
    for name, toks in skills.items():
        tf = Counter(toks)
        v = {t: c * idf[t] for t, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1
        vecs[name] = {t: x / norm for t, x in v.items()}
    return idf, vecs


def rank(prompt, idf, vecs):
    tf = Counter(t for t in tokens(prompt) if t in idf)
    q = {t: c * idf[t] for t, c in tf.items()}
    norm = math.sqrt(sum(x * x for x in q.values())) or 1
    scores = {name: sum(q[t] / norm * v.get(t, 0) for t in q) for name, v in vecs.items()}
    return sorted(scores, key=lambda k: -scores[k]), scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills", nargs="*")
    ap.add_argument("--collide", type=float, default=0.45, help="cosine above which two descriptions collide")
    args = ap.parse_args()

    skills = load_skills()
    idf, vecs = build_index(skills)
    case_dir = os.path.join(ROOT, "eval", "triggers")
    fails, total = [], 0
    for fname in sorted(os.listdir(case_dir)):
        case = json.load(open(os.path.join(case_dir, fname)))
        skill = case["skill"]
        if args.skills and skill not in args.skills:
            continue
        if skill not in skills:
            fails.append(f"{fname}: skill '{skill}' not found")
            continue
        for pos in case.get("positive", []):
            total += 1
            order, _ = rank(pos["prompt"], idf, vecs)
            k = pos.get("top_k", 3)
            if skill not in order[:k]:
                fails.append(f"{skill}: '{pos['prompt']}' → rank {order.index(skill) + 1} (want ≤{k}; top: {', '.join(order[:3])})")
        for neg in case.get("negative", []):
            total += 1
            order, _ = rank(neg["prompt"], idf, vecs)
            owner = neg.get("owner")
            if order[0] == skill:
                fails.append(f"{skill}: must not win '{neg['prompt']}' (owner {owner or '?'}, rank {order.index(owner) + 1 if owner in order else '-'})")
            elif owner and order.index(owner) > order.index(skill):
                fails.append(f"{skill}: outranks owner {owner} on '{neg['prompt']}'")

    names = sorted(vecs)
    collisions = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            sim = sum(x * vecs[b].get(t, 0) for t, x in vecs[a].items())
            if sim >= args.collide:
                collisions.append(f"{a} ~ {b}: {sim:.2f}")

    for c in collisions:
        print(f"warn  description collision {c}")
    for f in fails:
        print(f"FAIL  {f}")
    print(f"eval-triggers: {total - len(fails)}/{total} passed, {len(collisions)} collision warning(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
