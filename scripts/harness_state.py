"""Test helper: importing it points XDG_DATA_HOME at a temp dir, so hooks write their state there, not in ~."""
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "plugins", "core", "hooks", "lib", "state-dir.sh")
os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="harness-data-")


def state_dir(repo):
    """The repo's personal state dir, computed by the same lib the hooks source."""
    return subprocess.run(["bash", "-c", '. "$1" && state_dir "$2"', "_", LIB, repo],
                          capture_output=True, text=True, check=True).stdout.strip()


def specs(repo, *parts):
    """<state>/specs/<parts>: where a hook now reads what used to be <repo>/specs/<parts>."""
    return os.path.join(state_dir(repo), "specs", *parts)
