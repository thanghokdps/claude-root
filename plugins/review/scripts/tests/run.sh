#!/usr/bin/env bash
# run.sh — runs validate-audit.py on every fixture pair and diffs exit code + output against expected.txt.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VALIDATOR="$HERE/../validate-audit.py"
failed=0
for dir in "$HERE"/*/; do
  name="$(basename "$dir")"
  actual="$(python3 -I "$VALIDATOR" "$dir" --summary; echo "exit $?")"
  # expected.txt puts the exit line first; the validator prints it last, so rotate before diffing.
  expected="$(tail -n +2 "$dir/expected.txt"; head -n 1 "$dir/expected.txt")"
  if [ "$actual" == "$expected" ]; then
    echo "ok   $name"
  else
    echo "FAIL $name"
    diff <(echo "$expected") <(echo "$actual")
    failed=1
  fi
done
[ "$failed" -eq 0 ] && echo "validate-audit: $(ls -d "$HERE"/*/ | wc -l | tr -d ' ') fixtures passed"
exit "$failed"
