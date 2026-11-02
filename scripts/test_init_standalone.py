#!/usr/bin/env python3
"""STANDALONE=1 init.sh copies hooks that still run from the project. Run: python3 scripts/test_init_standalone.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INIT = os.path.join(ROOT, "plugins", "core", "scripts", "init.sh")


def test_copied_guards_hooks_find_their_helper():
    project = tempfile.mkdtemp(prefix="init-standalone-")
    subprocess.run(["git", "-C", project, "init", "-q", "-b", "feat/x"], check=True)
    env = {**os.environ, "STANDALONE": "1"}
    subprocess.run(["bash", INIT, project], capture_output=True, text=True, env=env, check=True, timeout=120)
    hooks = os.path.join(project, ".claude", "hooks")
    assert os.path.isfile(os.path.join(hooks, "lib", "project-dir.sh"))
    os.makedirs(os.path.join(project, "specs"), exist_ok=True)
    with open(os.path.join(project, "specs", "HANDOFF.md"), "w") as f:
        f.write("PROJECT-HANDOFF\n")
    out = subprocess.run([os.path.join(hooks, "session-resume.sh")], input=json.dumps({"cwd": project}),
                         capture_output=True, text=True, env={**os.environ, "CLAUDE_PROJECT_DIR": project})
    assert "PROJECT-HANDOFF" in out.stdout and "command not found" not in out.stderr, out.stderr


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_init_standalone: {len(tests)} passed")
