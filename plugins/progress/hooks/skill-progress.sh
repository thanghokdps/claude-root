#!/usr/bin/env bash
# skill-progress.sh — checklist and live progress for any skill with "## Step" / "## Stage" headings.
#   Skill invoked (PostToolUse:Skill, UserPromptExpansion) → inject its steps + "Done when" lines as a checklist
#     Claude tracks with TaskCreate/TaskUpdate, and tell the user how many checkpoints it has.
#   TaskCreated / TaskCompleted → count per session; each completion shows "✅ (done/total) <subject>".
#   Stop → "🏁 checklist complete" once, or what is still open. Sessions without task tools (TaskCreate is off unless
#     the todo panel is enabled) are counted from "✅ <step>" / "⏭ <step>" lines in Claude's last reply.
# Never blocks: always exits 0 (exit 2 on TaskCompleted would refuse the completion).
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"
STATE_DIR="${CLAUDE_PLUGIN_DATA:-$HOME/.claude/plugins/data/progress}"
mkdir -p "$STATE_DIR" 2>/dev/null || exit 0

HOOK_INPUT="$INPUT" python3 -I - "$STATE_DIR" "${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}" <<'PY' || true
import glob, json, os, re, sys, time

state_dir, plugin_root = sys.argv[1], sys.argv[2]
try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    sys.exit(0)
event = ev.get("hook_event_name", "")
session = re.sub(r"[^\w-]", "", ev.get("session_id") or "default")
path = os.path.join(state_dir, f"{session}.json")
try:
    st = json.load(open(path))
except (OSError, ValueError):
    st = {"tasks": {}, "order": [], "skill": None, "skill_at": 0, "reported": ""}
st.setdefault("checklist", [])
if not isinstance(st.get("marked"), dict):
    st["marked"] = {}  # title → "done" | "skipped"


def save():
    tmp = path + ".tmp"
    json.dump(st, open(tmp, "w"))
    os.replace(tmp, path)


def emit(out):
    print(json.dumps(out, ensure_ascii=False))


def find_skill(name):
    """SKILL.md for 'plugin:skill' or 'skill': sibling plugins (kit checkout or plugin cache), project, user."""
    plugin, _, skill = name.rpartition(":")
    pat = re.escape(skill)
    roots = [os.path.join(plugin_root, "..", plugin or "*"),                       # plugins/<p>/
             os.path.join(plugin_root, "..", "..", plugin or "*", "*"),            # cache/<mkt>/<p>/<version>/
             os.path.join(ev.get("cwd") or ".", ".claude"), os.path.expanduser("~/.claude")]
    for root in roots:
        hits = sorted(glob.glob(os.path.join(root, "skills", skill, "SKILL.md")))
        if hits:
            return hits[-1]
    return None


def checklist(md):
    """[(title, done_when)]: '##'/'###' Step|Stage|Phase headings, plus any heading with a '**Done when:**' under it."""
    heads, cur = [], None
    for line in open(md, encoding="utf-8"):
        h = re.match(r"^#{2,3}\s+(.+)$", line.strip())
        if h:
            cur = [h.group(1).strip(), ""]
            heads.append(cur)
            continue
        d = re.match(r"^\*\*Done when:\*\*\s*(.+)$", line.strip())
        if d and cur is not None and not cur[1]:
            cur[1] = d.group(1).strip()
    return [tuple(h) for h in heads if h[1] or re.match(r"(Step|Stage|Phase)\b", h[0])]


if event in ("PostToolUse", "UserPromptExpansion"):
    name = (ev.get("tool_input") or {}).get("skill") if event == "PostToolUse" else ev.get("command_name")
    if not name:
        sys.exit(0)
    now = time.time()
    if st.get("skill") == name and now - st.get("skill_at", 0) < 30:
        sys.exit(0)  # the same invocation seen by both events
    md = find_skill(name)
    items = checklist(md) if md else []
    if len(items) < 2:
        sys.exit(0)
    st.update(skill=name, skill_at=now, checklist=[t for t, _ in items], marked={}, reported="")
    save()
    short = name.rpartition(":")[2]
    lines = [f"- [ ] {t}" + (f" — done when: {d}" if d else "") for t, d in items]
    emit({
        "systemMessage": f"📋 /{short} — {len(items)} checkpoints: " + " · ".join(t.split(" — ", 1)[-1] for t, _ in items),
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": (
                f"Progress checklist for /{short}. If the TaskCreate tool is available, create one task per line before "
                "the first step (subject = the step title; skip steps this run does not reach) and complete each only when "
                "its done-when condition holds. Without TaskCreate, end each finished step with its own line "
                "`✅ <step title>`, and a step this run skips with `⏭ <step title>`. Either way the user sees the tally, so mark a step only with its evidence shown.\n"
                + "\n".join(lines)),
        },
    })

elif event == "TaskCreated":
    tid = str(ev.get("task_id") or "")
    if tid and tid not in st["tasks"]:
        st["tasks"][tid] = {"subject": ev.get("task_subject") or tid, "done": False}
        st["order"].append(tid)
        st["reported"] = ""
        save()

elif event == "TaskCompleted":
    tid = str(ev.get("task_id") or "")
    task = st["tasks"].setdefault(tid, {"subject": ev.get("task_subject") or tid, "done": False})
    if tid not in st["order"]:
        st["order"].append(tid)
    task["done"] = True
    save()
    done = sum(t["done"] for t in st["tasks"].values())
    emit({"systemMessage": f"✅ ({done}/{len(st['tasks'])}) {task['subject']}"})

elif event == "Stop":
    tasks = [st["tasks"][i] for i in st["order"] if i in st["tasks"]]
    if not tasks and st["checklist"]:
        # No task tools in this session: count the "✅ <step>" lines Claude wrote against the checklist.
        for line in (ev.get("last_assistant_message") or "").splitlines():
            m = re.match(r"^[^\w✅⏭]*(✅|⏭)\ufe0f?\s*(.+)$", line.strip())
            if not m:
                continue
            mark, said = ("done" if m.group(1) == "✅" else "skipped"), m.group(2).strip(" *_`").lower()
            if len(said) < 4:
                continue  # "✅ ok" names no step
            for title in st["checklist"]:
                head = title.split(" — ")[0].lower()
                if title not in st["marked"] and (title.lower() in said or said.startswith(head) or said in title.lower()):
                    st["marked"][title] = mark
                    break
        tasks = [{"subject": t, "done": st["marked"].get(t) == "done", "skipped": st["marked"].get(t) == "skipped"}
                 for t in st["checklist"]]
        if not st["marked"]:
            sys.exit(0)  # nothing reported yet — stay quiet rather than print 0/N every turn
    if not tasks:
        sys.exit(0)
    done = sum(t["done"] for t in tasks)
    skipped = sum(t.get("skipped", False) for t in tasks)
    left = [t["subject"] for t in tasks if not t["done"] and not t.get("skipped")]
    key = f"{done}/{skipped}/{len(tasks)}"
    if key == st.get("reported"):
        sys.exit(0)  # nothing changed since the last report
    st["reported"] = key
    save()
    skill = f" for /{st['skill'].rpartition(':')[2]}" if st.get("skill") else ""
    also = f" · ⏭ {skipped} skipped" if skipped else ""
    if left:
        emit({"systemMessage": f"⏳ {done}/{len(tasks)} done{also} — open: " + " · ".join(left[:4]) + (" …" if len(left) > 4 else "")})
    elif done == len(tasks):
        emit({"systemMessage": f"🏁 Checklist complete — {done}/{len(tasks)}{skill}"})
    else:  # nothing open, but not everything was done: never call that complete
        emit({"systemMessage": f"⏹ Checklist closed{skill} — ✅ {done} done{also}"})
PY
exit 0
