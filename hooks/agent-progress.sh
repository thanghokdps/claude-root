#!/bin/bash
# PostToolUse(Agent|Edit|Write|Bash) + PreToolUse(Agent)
# Prints live agent/wave progress to terminal via stderr.
# Pass "pre" as $1 for PreToolUse, default is post.

INPUT=$(cat /dev/stdin)
HOOK_TYPE="${1:-post}"
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
TS=$(date "+%H:%M:%S")

# ANSI colors
MAG='\033[0;35m'; BOLD_MAG='\033[1;35m'
GRN='\033[0;32m'; BOLD_GRN='\033[1;32m'
CYN='\033[0;36m'; BOLD_CYN='\033[1;36m'
YLW='\033[1;33m'
BLU='\033[0;34m'; BOLD_BLU='\033[1;34m'
RED='\033[0;31m'
DIM='\033[2m'; BOLD='\033[1m'
RST='\033[0m'

# Print wave board from WAVE_STATE.json if it exists
print_wave_board() {
  STATE_FILE=$(find "$(pwd)/specs" -name "WAVE_STATE.json" 2>/dev/null | xargs ls -t 2>/dev/null | head -1)
  [ -z "$STATE_FILE" ] && return

  SLUG=$(python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(d.get('slug',''))" 2>/dev/null)
  ISSUE=$(python3 -c "import json,sys; d=json.load(open('$STATE_FILE')); print(d.get('issue',''))" 2>/dev/null)

  echo -e "${BOLD_BLU}┌─ 🌊 WAVE BOARD ── ${ISSUE} ${SLUG} ──────────────────────────${RST}" >&2

  python3 - "$STATE_FILE" <<'PYEOF' 1>&2 2>/dev/null
import json, sys

COLORS = {
  "completed": "\033[1;32m✅\033[0m",
  "in_progress": "\033[0;34m🔵\033[0m",
  "pending": "\033[2m⬜\033[0m",
  "failed": "\033[0;31m❌\033[0m",
}
AGENT_COLOR = "\033[0;36m"
RST = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
YLW = "\033[1;33m"

data = json.load(open(sys.argv[1]))
waves = data.get("waves", [])
for wi, wave in enumerate(waves):
  tasks = wave.get("tasks", [])
  is_parallel = len(tasks) > 1
  wave_num = wave.get("wave", wi + 1)
  sep = f"│  {'─' * 64}"

  for ti, task in enumerate(tasks):
    status = task.get("status", "pending")
    icon = COLORS.get(status, "⬜")
    title = task.get("title", "")[:42]
    agent = task.get("agent", "")
    blocked_by = task.get("blocked_by", [])
    is_now = status == "in_progress"

    wave_label = f"Wave {wave_num}" if ti == 0 else "       "
    parallel_tag = ""
    if is_parallel:
      if ti == 0:
        parallel_tag = f" {DIM}┐ parallel{RST}"
      elif ti == len(tasks) - 1:
        parallel_tag = f" {DIM}┘ parallel{RST}"
      else:
        parallel_tag = f" {DIM}│ parallel{RST}"

    blocked_tag = ""
    if blocked_by:
      blocked_tag = f"  {DIM}← blocked by #{','.join(str(b) for b in blocked_by)}{RST}"

    now_tag = f"  {YLW}← NOW{RST}" if is_now else ""

    agent_str = f"[{AGENT_COLOR}{agent}{RST}]" if agent else ""
    print(f"│  {wave_label}  {icon}  {title:<44} {agent_str}{parallel_tag}{blocked_tag}{now_tag}")

  if wi < len(waves) - 1:
    print(sep)

PYEOF

  echo -e "${BOLD_BLU}└──────────────────────────────────────────────────────────────${RST}" >&2
}

case "$TOOL" in
  Agent)
    DESC=$(echo "$INPUT" | jq -r '.tool_input.description // "agent"' 2>/dev/null)
    SUBTYPE=$(echo "$INPUT" | jq -r '.tool_input.subagent_type // "general-purpose"' 2>/dev/null)
    BG=$(echo "$INPUT" | jq -r '.tool_input.run_in_background // false' 2>/dev/null)

    if [ "$BG" = "true" ]; then
      MODE="${YLW}⚡ PARALLEL (background)${RST}"
    else
      MODE="${RED}🔒 SEQUENTIAL (blocking)${RST}"
    fi

    if [ "$HOOK_TYPE" = "pre" ]; then
      echo "" >&2
      print_wave_board
      echo "" >&2
      echo -e "${BOLD_MAG}┌─ 🤖 AGENT SPAWN ─────────────────────────────────────────${RST}" >&2
      echo -e "${MAG}│  [$TS]  ${BOLD}${SUBTYPE}${RST}" >&2
      echo -e "${MAG}│  Task: ${DESC}${RST}" >&2
      echo -e "${MAG}│  Mode: ${MODE}" >&2
      echo -e "${BOLD_MAG}└──────────────────────────────────────────────────────────${RST}" >&2
    else
      echo -e "${BOLD_GRN}✅ [$TS] AGENT DONE  ${DESC}${RST}" >&2
      echo "" >&2
      print_wave_board
    fi
    ;;

  Edit)
    FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // "unknown"' 2>/dev/null | sed "s|$(pwd)/||")
    echo -e "${CYN}  ✏️  [$TS] EDIT   ${FILE}${RST}" >&2
    ;;

  Write)
    FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // "unknown"' 2>/dev/null | sed "s|$(pwd)/||")
    echo -e "${CYN}  📝 [$TS] WRITE  ${FILE}${RST}" >&2
    ;;

  Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null | head -1 | cut -c1-72)
    echo "$CMD" | grep -qE 'npm|pnpm|yarn|git (commit|push|diff|status)|tsc|jest|eslint|pytest|ruff' || exit 0
    echo -e "${YLW}  💻 [$TS] BASH   ${CMD}${RST}" >&2
    ;;
esac

exit 0
