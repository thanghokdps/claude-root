#!/usr/bin/env bash
# Warn-only freshness check: latest npm version of each vendor package the agent references cite,
# and how old each reference's "checked against … on YYYY-MM-DD" line is. Needs the network, so it
# stays out of check.sh; always exits 0.
#   bash scripts/check-upstream.sh            # warn when a reference is older than 30 days
#   MAX_AGE_DAYS=14 bash scripts/check-upstream.sh
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
max_age="${MAX_AGE_DAYS:-30}"

online=1
npm ping >/dev/null 2>&1 || online=0
[ "$online" = 1 ] || echo "notice: npm registry unreachable — latest versions skipped, dates still checked"

while IFS=$'\t' read -r pkg refs; do
  latest="-"
  [ "$online" = 1 ] && latest="$(npm view "$pkg" version 2>/dev/null || echo '?')"
  printf '%s\t%s\t%s\n' "$pkg" "$latest" "$refs"
done < <(python3 -I -c 'import json,sys; [print(p, ",".join(r), sep="\t") for p, r in json.load(open(sys.argv[1])).items()]' "$root/scripts/upstream.json") |
python3 -I -c '
import re, sys, datetime
root, max_age = sys.argv[1], int(sys.argv[2])
today = datetime.date.today()
stale = 0
row = "%-24s %-10s %-11s %4s  %s"
print(row % ("package", "latest", "checked", "age", "reference"))
for line in sys.stdin:
    pkg, latest, refs = line.rstrip("\n").split("\t")
    for ref in refs.split(","):
        try:
            text = open(root + "/" + ref).read()
        except OSError:
            print(row % (pkg, latest, "missing", "", ref)); stale += 1; continue
        m = re.search(r"[Cc]hecked against[^\n]*?(\d{4}-\d{2}-\d{2})", text)
        if not m:
            print(row % (pkg, latest, "undated", "", ref)); stale += 1; continue
        age = (today - datetime.date.fromisoformat(m.group(1))).days
        flag = "  ⚠ re-check" if age > max_age else ""
        stale += bool(flag)
        print(row % (pkg, latest, m.group(1), age, ref + flag))
print("\n%d reference(s) to re-check (older than %d days, undated or missing)" % (stale, max_age))
' "$root" "$max_age"
exit 0
