---
model: opus
effort: high
name: container
description: Writes or changes a Dockerfile or compose service the way the repo already builds images — multi-stage build, pinned base image by digest, non-root user, only runtime files copied, a healthcheck, secrets never baked in, a .dockerignore that keeps the context small. Proves it by building the image, running it, and passing its healthcheck. Use when the user asks to containerise a service, fix a Dockerfile, shrink an image, add a compose service, or when a build copies secrets or runs as root.
when_to_use: Dockerfile, "viết Dockerfile", containerise this service, docker compose service, image too big, multi-stage build, run as non-root, healthcheck, pin base image, .dockerignore, secret in image layer, build arg vs env
---

# container

**Invoke:** `/container <service, its runtime, and where the image runs>`

Rules: `${CLAUDE_PLUGIN_ROOT}/rules/container.md`, `security.md` from core. The pipeline that builds and pushes the image is `/pipeline`; the cluster or service it runs on is `/infra-change`.

---

## Step 1 — Detect

| Piece | Look for |
|-------|----------|
| Existing images | `Dockerfile*`, `docker-compose*.yml`, `.dockerignore`, a base-image convention across services |
| Runtime | the start command, port, the env the app reads at boot (its env schema), writable paths |
| Build | package manager and lockfile, build vs runtime dependencies, native modules |
| Registry | where images go, tag scheme, how CI builds them |

**Done when:** each row names a path, and the image's contract is stated: base, port, start command, env it needs, volumes.

## Step 2 — Write the Dockerfile the way the repo does

- Multi-stage when there is a build or install step: a build stage with the toolchain, a runtime stage with only the built output and production dependencies. No build and no dependencies → one pinned stage with only the runtime files.
- Base image pinned by tag **and** digest; the same family as the repo's other services.
- A non-root user owning only the paths it writes; `WORKDIR` set; no `latest`, no `curl | sh`.
- Secrets never in a layer: no `COPY .env`, no `ARG` holding a token; runtime secrets arrive as env or mounted files.
- `HEALTHCHECK` on the app's own health route; `.dockerignore` excludes `.git`, `node_modules`, tests, docs, local env files.
- Compose: one service per process, `depends_on` with conditions, env from a file that is ignored by git, named volumes for state.

**Done when:** `docker build` succeeds and `hadolint` (when installed) reports nothing above info.

## Step 3 — Prove it

Build, run, hit the healthcheck and one real route; compare the image size and layer count with the previous image (`docker history`). Quote the sizes and the healthcheck result.

**Done when:** the container is healthy from a clean build, the size did not grow without a reason, and `docker run` as the non-root user serves the route.

---

Hand-offs: the CI job that builds and pushes it → `/pipeline` · the cluster or service it runs on → `/infra-change` · done → `/verify-done` → `/review-checklist`.
