"""Isolation for running agent-generated code.

The whole premise of this harness is that the code under test was written by an
agent — which means it is untrusted. Two things run it: the solver command, and
pytest during grading. Both must be contained.

Two runners:

  DockerRunner  — one `docker run --rm` per command, network disabled, workdir
                  bind-mounted, container filesystem discarded afterwards.
  LocalRunner   — subprocess on the host. Requires an explicit opt-in flag, and
                  even then the environment is scrubbed so generated code cannot
                  read the operator's credentials.

Both scrub the environment. `os.environ` on a developer machine holds
ANTHROPIC_API_KEY, AWS creds, GH tokens — none of which any evaluated task needs.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

#: Names matching these are never passed through to evaluated code.
_SECRET_PATTERN = re.compile(
    r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH|SESSION|COOKIE|PRIVATE)",
    re.IGNORECASE,
)

#: The only host variables an evaluated task legitimately needs.
_ALLOWED = ("PATH", "HOME", "LANG", "LC_ALL", "TZ", "TMPDIR")


def scrubbed_env(workdir: str, extra: dict | None = None) -> dict:
    """A minimal environment: allowlisted host vars, no secrets, workdir importable."""
    env = {k: os.environ[k] for k in _ALLOWED if k in os.environ}
    env["PYTHONPATH"] = workdir
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for key, value in (extra or {}).items():
        if _SECRET_PATTERN.search(key):
            raise ValueError(f"refusing to pass {key} into the sandbox — it looks like a secret")
        env[key] = value
    return env


class LocalRunner:
    """Runs on the host. Isolation is a temp dir and a scrubbed env — nothing more."""

    name = "local"
    sandboxed = False

    def run(self, argv, workdir: str, timeout: int, env_extra: dict | None = None, shell: bool = False):
        return subprocess.run(
            argv,
            cwd=workdir,
            env=scrubbed_env(workdir, env_extra),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
        )


class DockerRunner:
    """Runs each command in a throwaway container with networking disabled."""

    name = "docker"
    sandboxed = True

    def __init__(self, image: str, memory: str = "512m", cpus: str = "1"):
        self.image = image
        self.memory = memory
        self.cpus = cpus

    def run(self, argv, workdir: str, timeout: int, env_extra: dict | None = None, shell: bool = False):
        inner = argv if isinstance(argv, str) else " ".join(_quote(a) for a in argv)
        env_args = []
        for key, value in scrubbed_env("/work", env_extra).items():
            env_args += ["-e", f"{key}={value}"]
        docker_argv = [
            "docker", "run", "--rm",
            "--network", "none",             # generated code gets no egress
            "--memory", self.memory,
            "--cpus", self.cpus,
            "--pids-limit", "256",
            "-v", f"{workdir}:/work",
            "-w", "/work",
            *env_args,
            self.image,
            "sh", "-c", inner,
        ]
        return subprocess.run(
            docker_argv, capture_output=True, text=True, timeout=timeout + 30
        )


def _quote(arg: str) -> str:
    return "'" + str(arg).replace("'", "'\\''") + "'"


def docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=15
        ).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def image_exists(image: str) -> bool:
    try:
        return subprocess.run(
            ["docker", "image", "inspect", image], capture_output=True, timeout=30
        ).returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


BUILD_HINT = """\
Sandbox image '{image}' not found. Build it once:

    docker build -t {image} {context}

Or run without isolation — only do this if you trust the solver:

    python -m evalkit.cli run --sandbox none --allow-unsandboxed
"""


def build_runner(mode: str, image: str, allow_unsandboxed: bool, context: str):
    """Resolve --sandbox into a runner, refusing to run unsandboxed by accident."""
    if mode == "none":
        if not allow_unsandboxed:
            raise SystemExit(
                "Refusing to run agent-generated code on the host without --allow-unsandboxed.\n"
                "The solver command and pytest both execute untrusted code."
            )
        return LocalRunner()

    if mode == "docker":
        if not docker_available():
            raise SystemExit(
                "--sandbox docker requested but Docker is not available.\n"
                "Start Docker, or pass --sandbox none --allow-unsandboxed."
            )
        if not image_exists(image):
            raise SystemExit(BUILD_HINT.format(image=image, context=context))
        return DockerRunner(image)

    if mode == "auto":
        if docker_available() and image_exists(image):
            return DockerRunner(image)
        if allow_unsandboxed:
            return LocalRunner()
        raise SystemExit(
            BUILD_HINT.format(image=image, context=context)
            + "\n(--sandbox auto found no usable Docker image and no opt-out flag.)"
        )

    raise SystemExit(f"unknown --sandbox mode: {mode}")
