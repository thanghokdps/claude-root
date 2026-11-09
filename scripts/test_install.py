#!/usr/bin/env python3
"""Tests for the pack-disable step of scripts/install.sh, against a fake `claude`. Run: python3 scripts/test_install.py"""
import glob
import json
import os
import shutil
import stat
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKS = ("ai", "frontend", "backend", "mobile", "devops", "workplace", "reverse")

# Refuses what the CLI refuses (2.1.317): a plugin an enabled plugin requires, and one already disabled.
# Dependencies come from the real plugin.json files, so a new dependency between packs is covered too.
FAKE_CLAUDE = r"""#!/usr/bin/env python3
import glob, json, os, sys
kit, state = os.environ["FAKE_KIT"], os.environ["FAKE_STATE"]
args = sys.argv[1:]
on = set(json.load(open(state)))

def requires(plugin):
    return json.load(open(os.path.join(kit, "plugins", plugin, ".claude-plugin", "plugin.json"))).get("dependencies", [])

if args[:3] == ["plugin", "marketplace", "list"]:
    print(f"  ❯ harness\n    Source: Folder ({kit})")
elif args[:2] == ["plugin", "uninstall"]:
    on.discard(args[2].split("@")[0])
elif args[:2] == ["plugin", "install"]:
    name = args[2].split("@")[0]
    if name not in os.environ.get("FAKE_INSTALLS_OFF", "").split():
        on.add(name)
elif args[:2] == ["plugin", "disable"]:
    name = args[2].split("@")[0]
    dependents = sorted(p for p in on if name in requires(p))
    if name in os.environ.get("FAKE_STUCK", "").split():
        sys.exit(f'✘ Failed to disable plugin "{args[2]}": permission denied')
    if name not in on:
        sys.exit(f'✘ Failed to disable plugin "{args[2]}": Plugin "{args[2]}" is already disabled at user scope')
    if dependents:
        sys.exit(f'✘ Failed to disable plugin "{args[2]}": {name} is still required by {dependents[0]}')
    on.discard(name)
    print(f"✔ Successfully disabled plugin: {name} (scope: user)")
json.dump(sorted(on), open(state, "w"))
"""


def kit_copy(base):
    """The files install.sh reads, outside any git repo so remote-drift.sh stays offline."""
    kit = os.path.join(base, "kit")
    for name in ("global/CLAUDE.md", ".claude-plugin/marketplace.json", "scripts/install.sh", "scripts/remote-drift.sh"):
        os.makedirs(os.path.dirname(os.path.join(kit, name)), exist_ok=True)
        shutil.copy(os.path.join(ROOT, name), os.path.join(kit, name))
    shutil.copytree(os.path.join(ROOT, "plugins/core/rules"), os.path.join(kit, "plugins/core/rules"))
    shutil.copytree(os.path.join(ROOT, "plugins/guards/hooks"), os.path.join(kit, "plugins/guards/hooks"))
    for manifest in glob.glob(os.path.join(ROOT, "plugins/*/.claude-plugin/plugin.json")):
        target = os.path.join(kit, os.path.relpath(manifest, ROOT))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(manifest, target)
    return kit


def install(**env):
    """Run install.sh; returns its stdout and the plugins left enabled."""
    base = tempfile.mkdtemp(prefix="install-")
    kit, home, bin_dir = kit_copy(base), os.path.join(base, "home"), os.path.join(base, "bin")
    state = os.path.join(base, "enabled.json")
    os.makedirs(os.path.join(home, ".claude"))
    os.makedirs(bin_dir)
    with open(state, "w") as f:
        json.dump([], f)
    fake = os.path.join(bin_dir, "claude")
    with open(fake, "w") as f:
        f.write(FAKE_CLAUDE)
    os.chmod(fake, os.stat(fake).st_mode | stat.S_IEXEC)
    full_env = {**os.environ, "HOME": home, "PATH": f"{bin_dir}:{os.environ['PATH']}",
                "FAKE_KIT": kit, "FAKE_STATE": state, **env}
    r = subprocess.run(["bash", os.path.join(kit, "scripts", "install.sh")], capture_output=True, text=True, env=full_env)
    assert r.returncode == 0, r.stdout + r.stderr
    with open(state) as f:
        return r.stdout, set(json.load(f))


def test_every_pack_ends_off_and_the_process_plugins_stay_on():
    out, enabled = install()
    assert not enabled & set(PACKS), (enabled, out)
    assert {"core", "dev", "harness"} <= enabled, enabled
    assert "WARN" not in out, out
    assert "packs off at user scope" in out, out


def test_a_pack_that_cannot_be_disabled_is_named_and_the_summary_says_so():
    out, enabled = install(FAKE_STUCK="mobile")
    assert enabled & set(PACKS) == {"mobile"}, enabled
    assert "WARN mobile stays on at user scope — ✘ Failed" in out, out
    assert "still on at user scope, loaded in every repo: mobile" in out, out
    assert "packs off at user scope" not in out, out


def test_a_pack_already_off_is_no_warning():
    out, enabled = install(FAKE_INSTALLS_OFF="workplace")
    assert not enabled & set(PACKS), enabled
    assert "WARN" not in out, out
    assert "packs off at user scope" in out, out


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"install tests: {len(tests)} passed")
