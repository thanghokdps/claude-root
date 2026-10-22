#!/bin/bash

# PostToolUse(Edit|Write): flag edits to files outside the active PLAN.md <files> set.
# WARN by default. Set BLAST_RADIUS_STRICT=1 to block (exit 2).

INPUT=$(cat /dev/stdin)
FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -z "$FILE" ] && exit 0

REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null)"
[ -z "$REPO_DIR" ] && exit 0

REPO_DIR="$(cd "$REPO_DIR" 2>/dev/null && pwd -P)"
if [ -e "$FILE" ]; then
  FILE="$(cd "$(dirname "$FILE")" 2>/dev/null && pwd -P)/$(basename "$FILE")"
fi

REL="${FILE#"$REPO_DIR"/}"

# Skip bookkeeping / non-implementation files
case "$REL" in
  specs/*|docs/*|*.md|.claude/*) exit 0 ;;
esac

# Find the active PLAN.md
PLAN=""
for p in $(ls -t "$REPO_DIR"/specs/*/PLAN.md 2>/dev/null); do
  if grep -qiE '^status:[[:space:]]*active' "$p"; then PLAN="$p"; break; fi
done
[ -z "$PLAN" ] && PLAN=$(ls -t "$REPO_DIR"/specs/*/PLAN.md 2>/dev/null | head -1)
[ -z "$PLAN" ] && exit 0

DECLARED=$(grep -oE '<files>[^<]*</files>' "$PLAN" 2>/dev/null \
  | sed -E 's#</?files>##g' | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//' | grep -v '^$')
[ -z "$DECLARED" ] && exit 0

INSCOPE=0
bREL=$(basename "$REL")
while IFS= read -r d; do
  [ -z "$d" ] && continue
  [ "$REL" = "$d" ] && INSCOPE=1 && break
  case "$REL" in */"$d") INSCOPE=1; break ;; esac
  [ "$bREL" = "$(basename "$d")" ] && INSCOPE=1 && break
done <<EOF
$DECLARED
EOF

[ "$INSCOPE" -eq 1 ] && exit 0

if [ "${BLAST_RADIUS_STRICT:-0}" = "1" ]; then
  echo "[BLAST RADIUS] $REL is outside the active plan's <files> set." >&2
  echo " Scope creep — add the file to the plan or escalate." >&2
  exit 2
fi

jq -cn --arg f "$REL" --arg p "${PLAN#"$REPO_DIR"/}" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("blast-radius: edited " + $f + " which is NOT in the active plan <files> set (" + $p + "). If intentional, add it to the plan; otherwise treat as scope creep.")
  }
}'

exit 0
