#!/usr/bin/env bash
# learn-capture.sh — lessons capture themselves: every 50 tool calls a background haiku reflector proposes them.
# PreToolUse (every tool): counts calls in <git-common-dir>/claude-learn/<session_id>.count; a Read of a
#   .claude/docs/solutions/*.md lesson marks it used (learn-promote.py --touch), so it is not retired.
# Stop: at >= 50 calls it resets the count, writes a digest of the transcript since the last run (user and
#   assistant text plus tool names; never tool input or output; secret-patterns.txt scrubbed; last ~20 KB)
#   to claude-learn/digests/, and starts `claude -p --model haiku` in the background with learn-reflector.md
#   filled in. The child has no tools and replies with a JSON array; the hook writes each lesson to
#   claude-learn/queue/ (an unparsable reply is queued raw, so it shows up in queue/rejected/).
#   learn-promote.py validates and lands them at the next SessionStart. Parallel tool calls can race the count; it is a cadence, not a meter.
# HARNESS_LEARN=0 turns it off; HARNESS_LEARN_CHILD=1 (set on the child) stops it reflecting on itself.
# Never blocks: any failure exits 0.
[ "${HARNESS_LEARN:-1}" = "0" ] && exit 0
[ -n "${HARNESS_LEARN_CHILD:-}" ] && exit 0
INPUT="$(cat)"
HERE="$(cd "$(dirname "$0")" && pwd)"
PROMOTE="$HERE/../scripts/learn-promote.py"

FLAT="$(printf '%s' "$INPUT" | tr -d '\n')"
field() { printf '%s' "$FLAT" | sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p"; }
EVENT="$(field hook_event_name)"
SID="$(field session_id)"
case "$SID" in '' | *[!A-Za-z0-9_-]*) exit 0 ;; esac
CWD="$(field cwd)"
GITDIR="$(git -C "${CWD:-.}" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || exit 0
STATE="$GITDIR/claude-learn"
mkdir -p "$STATE" 2>/dev/null || exit 0
COUNT_FILE="$STATE/$SID.count"
COUNT="$(cat "$COUNT_FILE" 2>/dev/null)"
case "$COUNT" in '' | *[!0-9]*) COUNT=0 ;; esac

if [ "$EVENT" = "PreToolUse" ]; then
  printf '%s' $((COUNT + 1)) >"$COUNT_FILE" 2>/dev/null
  if [ "$(field tool_name)" = "Read" ]; then
    FILE="$(field file_path)"
    case "$FILE" in */docs/solutions/*.md) python3 -I "$PROMOTE" --touch "$FILE" >/dev/null 2>&1 ;; esac
  fi
  exit 0
fi

[ "$EVENT" = "Stop" ] || exit 0
[ "$COUNT" -ge 50 ] || exit 0
printf '0' >"$COUNT_FILE" 2>/dev/null
command -v claude >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0
TOP="$(git -C "${CWD:-.}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
RUN="$SID-$(date +%s)"
mkdir -p "$STATE/digests" "$STATE/queue" 2>/dev/null || exit 0

HOOK_INPUT="$INPUT" STATE="$STATE" RUN="$RUN" TOP="$TOP" HERE="$HERE" SID="$SID" python3 -I - <<'PY' || exit 0
import glob, json, os, re, sys

CAP = 20_000
env = os.environ
state, run, here = env["STATE"], env["RUN"], env["HERE"]
try:
    path = json.loads(env["HOOK_INPUT"]).get("transcript_path") or ""
    offset_file = os.path.join(state, env["SID"] + ".offset")
    try:
        offset = int(open(offset_file).read().strip())
    except (OSError, ValueError):
        offset = 0
    with open(path, "rb") as f:
        f.seek(0, 2)
        size = f.tell()
        f.seek(offset if offset <= size else 0)
        raw = f.read().decode("utf-8", "replace")
    open(offset_file, "w").write(str(size))
except Exception:
    sys.exit(1)

lines = []
for line in raw.splitlines():
    try:
        e = json.loads(line)
    except ValueError:
        continue
    role = e.get("type")
    if role not in ("user", "assistant") or e.get("isMeta"):
        continue
    content = (e.get("message") or {}).get("content")
    blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content or []
    parts = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "text" and (b.get("text") or "").strip():
            parts.append(b["text"].strip())
        elif b.get("type") == "tool_use":
            parts.append(f"[tool: {b.get('name')}]")
    if parts:
        lines.append(f"{role}: " + " ".join(parts))

patterns = []
for p in open(os.path.join(here, "secret-patterns.txt"), encoding="utf-8"):
    p = p.rstrip("\n")
    if p and not p.startswith("#"):
        patterns.append(re.compile(p))
text = "\n".join(lines)
for p in patterns:
    text = p.sub("[REDACTED]", text)
if len(text.encode()) > CAP:
    text = text.encode()[-CAP:].decode("utf-8", "ignore")
    text = text.split("\n", 1)[-1]
if not text.strip():
    sys.exit(1)

index = []
for idx in (os.path.join(env["TOP"], ".claude", "docs", "solutions", "INDEX.md"),
            os.path.expanduser("~/.claude/docs/solutions/INDEX.md")):
    try:
        index += [l for l in open(idx, encoding="utf-8").read().splitlines() if l.startswith("- [")]
    except OSError:
        pass
digests = os.path.join(state, "digests")
open(os.path.join(digests, run + ".txt"), "w").write(text + "\n")
prompt = open(os.path.join(here, "learn-reflector.md"), encoding="utf-8").read()
prompt = (prompt.replace("{{INDEX}}", "\n".join(index) or "(no lessons yet)")
          .replace("{{DIGEST}}", text))
open(os.path.join(digests, run + ".prompt"), "w").write(prompt)
# Keep the last 20 runs: learn-promote.py checks evidence quotes against these digests.
runs = sorted(glob.glob(os.path.join(digests, "*.txt")), key=os.path.getmtime)
for old in runs[:-20]:
    for f in (old, old[:-4] + ".prompt", old[:-4] + ".reply"):
        try:
            os.remove(f)
        except OSError:
            pass
PY

cd "$TOP" || exit 0
# No tools for the child: in dontAsk mode Claude Code refuses its writes under .git/, even with an allow rule.
(
  trap '' HUP
  HARNESS_LEARN_CHILD=1 claude -p --model haiku --no-session-persistence --tools "" \
    <"$STATE/digests/$RUN.prompt" >"$STATE/digests/$RUN.reply"
  STATE="$STATE" RUN="$RUN" python3 -I - <<'PY'
import json, os

state, run = os.environ["STATE"], os.environ["RUN"]
reply = open(os.path.join(state, "digests", run + ".reply"), encoding="utf-8", errors="replace").read()
try:
    lessons = json.loads(reply[reply.index("["):reply.rindex("]") + 1])
    if not isinstance(lessons, list):
        raise ValueError
    files = [(f"{run}-{i}.json", json.dumps(lesson, indent=1)) for i, lesson in enumerate(lessons)]
except ValueError:
    files = [(run + ".json", reply.strip())]
# Names never come from the reply; learn-promote.py takes the slug from the JSON.
for name, text in files:
    with open(os.path.join(state, "queue", name), "w", encoding="utf-8") as f:
        f.write(text + "\n")
PY
) </dev/null >/dev/null 2>&1 &
exit 0
