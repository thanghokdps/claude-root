#!/usr/bin/env bash
# statusline.sh — one line for Claude Code's status bar: model · branch #ticket · plan done/total task · ctx n% · lane.
# Contract (https://code.claude.com/docs/en/statusline, read 2026-10-30): stdin JSON with model.display_name,
# workspace.current_dir, transcript_path, context_window.{used_percentage,total_input_tokens,context_window_size};
# settings.json registers it as {"statusLine": {"type": "command", "command": "bash <path>"}}. The docs resolve
# ${CLAUDE_PLUGIN_ROOT} in hook, MCP, LSP and skill content only, so init.sh writes this file's absolute path.
# Never fails: any error prints the branch alone and exits 0. Colour only when ctx ≥ 70 (yellow) / ≥ 85 (red).
command -v python3 >/dev/null 2>&1 || exit 0
INPUT="$(cat)"

HOOK_INPUT="$INPUT" python3 -I - <<'PY' 2>/dev/null || true
import glob, json, os, re, subprocess, sys

WINDOW = 200_000  # the transcript fallback has no window size; the docs' default
SEP = " · "


def git(cwd, *args):
    try:
        r = subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def transcript_tokens(path):
    # Same read as core's compact-advisor: the last assistant usage is the context the model just saw.
    with open(path, "rb") as f:
        f.seek(0, 2)
        f.seek(max(0, f.tell() - 400_000))
        tail = f.read().decode("utf-8", "replace").splitlines()
    for line in reversed(tail):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        u = (e.get("message") or {}).get("usage") if e.get("type") == "assistant" else None
        if u:
            return sum(int(u.get(k) or 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
    return None


def context_pct(ev):
    cw = ev.get("context_window") or {}
    if cw.get("used_percentage") is not None:
        return int(float(cw["used_percentage"]))
    if cw.get("total_input_tokens") and cw.get("context_window_size"):
        return int(cw["total_input_tokens"]) * 100 // int(cw["context_window_size"])
    path = ev.get("transcript_path") or ""
    used = transcript_tokens(path) if os.path.isfile(path) else None
    return None if used is None else min(100, used * 100 // WINDOW)


def active_plan(root):
    plans = [p for p in glob.glob(os.path.join(root, "specs", "*", "PLAN.md"))
             if re.search(r"(?im)^\W*Status\W*:\W*active\b", open(p, encoding="utf-8", errors="replace").read())]
    return plans[0] if len(plans) == 1 else None


def plan_segment(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    tasks = re.findall(r'<task\b([^>]*)>(.*?)</task>', text, re.S)
    if not tasks:
        return None
    log = text.partition("## Status log")[2]
    done, current = 0, None
    for attrs, body in tasks:
        tid = (re.search(r'id="([^"]+)"', attrs) or [None, ""])[1]
        finished = re.search(r'status="(done|complete)"', attrs) or (
            tid and re.search(r"(?im)^.*\b%s\b.*\b(done|complete[d]?)\b" % re.escape(tid), log))
        if finished:
            done += 1
        elif current is None:
            action = re.search(r"<action>(.*?)</action>", body, re.S)
            current = " ".join((action.group(1) if action else "").split())
    seg = f"plan {done}/{len(tasks)}"
    if current:
        seg += " " + (current[:29] + "…" if len(current) > 30 else current)
    return seg


def lane_segment(plan_path):
    summary = os.path.join(os.path.dirname(plan_path), "SUMMARY.md")
    if not os.path.isfile(summary):
        return None
    m = re.search(r"(?im)^\W*Lane\W*:\W*(tiny|normal|high-risk)\b", open(summary, encoding="utf-8", errors="replace").read())
    return f"lane: {m.group(1).lower()}" if m else None


try:
    ev = json.loads(os.environ.get("HOOK_INPUT") or "{}")
except ValueError:
    ev = {}
if not isinstance(ev, dict):
    ev = {}
cwd = (ev.get("workspace") or {}).get("current_dir") or ev.get("cwd") or os.getcwd()
branch = git(cwd, "symbolic-ref", "--short", "HEAD")

segments = []
try:
    model = (ev.get("model") or {}).get("display_name")
    if model:
        segments.append(str(model))
    if branch:
        # Same shape ticket-gate.sh reads: <type>/<ID>-<slug> with ID = 412 or JIRA-412.
        m = re.match(r"^[\w.-]+/([A-Za-z]+-\d+|\d+)(?:[-_]|$)", branch)
        segments.append(branch + (f" #{m.group(1)}" if m else ""))
    root = git(cwd, "rev-parse", "--show-toplevel") or cwd
    plan = active_plan(root)
    if plan:
        seg = plan_segment(plan)
        if seg:
            segments.append(seg)
    pct = context_pct(ev)
    if pct is not None:
        colour = "\033[31m" if pct >= 85 else "\033[33m" if pct >= 70 else ""
        segments.append(f"{colour}ctx {pct}%{chr(27) + '[0m' if colour else ''}")
    if plan:
        lane = lane_segment(plan)
        if lane:
            segments.append(lane)
except Exception:
    segments = [branch] if branch else []
print(SEP.join(segments))
PY
exit 0
