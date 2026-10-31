---
type: llm
focus:
  source: file
  path: Dockerfile
---

This is the `Dockerfile` after the run. The original has `FROM node:latest`, runs as root, `COPY . .` of the whole context, and bakes `ENV PAYMENTS_API_KEY=sk_live_...` into a layer.

PASS if the Dockerfile is multi-stage, pins the base image by an exact tag or a digest (not `latest`), sets a non-root `USER`, and contains no secret value (the key arrives at runtime via env or a mounted file).
FAIL if `latest` stays, the process still runs as root, the key value stays in any `ENV`, `ARG` or `RUN`, or the file is unchanged.
