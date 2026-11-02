# Container rules — read by devops-engineer and container

- Multi-stage build when there is a build or install step: toolchain in the build stage, only built output and production dependencies in the runtime stage. An app with neither copies only its runtime files into one pinned stage.
- Base image pinned by tag and digest, from the same family the repo's other services use; rebuilt on a schedule so patches land.
- Non-root `USER` that owns only the paths it writes; no `sudo`, no `chmod 777`, no `curl | sh`.
- No secret in any layer: no `COPY .env`, no `ARG` carrying a token, no credential in a `RUN`. Runtime secrets arrive as env or mounted files.
- `HEALTHCHECK` on the application's own health route; the orchestrator's probes point at the same route.
- `.dockerignore` excludes `.git`, dependency folders, tests, docs and local env files, so the context and the image stay small and a secret file cannot slip in.
- One process per container; logs to stdout / stderr; state in a named volume or an external service, never in the writable layer.
- Compose for local and CI only: `depends_on` with conditions, env from a git-ignored file, pinned images.
