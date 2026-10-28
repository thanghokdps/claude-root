#!/usr/bin/env bash
# lock-tests.sh — freeze the regression test of a bug fix so the fix can't be made by editing the test.
# Usage: lock-tests.sh lock <file>… | check | unlock      (run from anywhere inside the git repo)
#   lock    records each file's sha256 in <git-dir>/claude-fix-lock.json (replaces an existing lock)
#   check   exit 0 when every locked file is unchanged (or no lock), exit 2 listing changed/missing files
#   unlock  removes the lock
# The test-lock hook (dev plugin) blocks edits to locked files while the lock exists.
command -v python3 >/dev/null 2>&1 || { echo "lock-tests: python3 is required" >&2; exit 2; }

usage() {
  echo "usage: lock-tests.sh lock <file>… | check | unlock" >&2
  exit 2
}
[ $# -ge 1 ] || usage

ACTION="$1"
shift
case "$ACTION" in
  lock) [ $# -ge 1 ] || usage ;;
  check | unlock) [ $# -eq 0 ] || usage ;;
  *) usage ;;
esac

GIT_DIR_ABS="$(git rev-parse --absolute-git-dir 2>/dev/null)" || { echo "lock-tests: not inside a git repo" >&2; exit 2; }
TOP="$(git rev-parse --show-toplevel)"
LOCK="$GIT_DIR_ABS/claude-fix-lock.json"

LOCK_FILE="$LOCK" LOCK_TOP="$TOP" LOCK_ACTION="$ACTION" python3 - "$@" <<'PY'
import hashlib, json, os, sys, datetime

lock, top, action = os.environ["LOCK_FILE"], os.environ["LOCK_TOP"], os.environ["LOCK_ACTION"]
top = os.path.realpath(top)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


if action == "lock":
    entries = []
    for arg in sys.argv[1:]:
        full = os.path.realpath(arg)
        if not os.path.isfile(full):
            print(f"lock-tests: {arg} does not exist", file=sys.stderr)
            sys.exit(2)
        rel = os.path.relpath(full, top)
        if rel.startswith(".."):
            print(f"lock-tests: {arg} is outside the repo", file=sys.stderr)
            sys.exit(2)
        entries.append({"path": rel, "sha256": sha(full)})
    when = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(lock, "w", encoding="utf-8") as f:
        json.dump({"files": entries, "locked": when}, f, indent=2)
    print("locked:")
    for e in entries:
        print(f"  {e['path']}  {e['sha256'][:12]}")
    sys.exit(0)

if action == "unlock":
    try:
        os.remove(lock)
        print("unlocked")
    except OSError:
        print("no lock")
    sys.exit(0)

try:
    data = json.load(open(lock, encoding="utf-8"))
except OSError:
    print("no lock")
    sys.exit(0)
except ValueError:
    print("lock-tests: lock file is unreadable; unlock and lock again", file=sys.stderr)
    sys.exit(2)

bad = []
for e in data.get("files", []):
    full = os.path.join(top, e["path"])
    if not os.path.isfile(full):
        bad.append(f"  missing: {e['path']}")
    elif sha(full) != e["sha256"]:
        bad.append(f"  changed: {e['path']}")
if bad:
    print("lock-tests: locked test files differ from when they were locked:", file=sys.stderr)
    print("\n".join(bad), file=sys.stderr)
    sys.exit(2)
print("lock intact")
PY
