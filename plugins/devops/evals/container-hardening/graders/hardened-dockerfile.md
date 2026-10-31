---
type: llm
---

Judge the Dockerfile the run proposes in its final reply: the kit's sensitive-path hook holds a Dockerfile edit for the user's approval, so in this sandbox the file itself stays unchanged and the reply carries the full proposed content. The original has `FROM node:latest`, runs as root, `COPY . .` of the whole context, `RUN npm install`, and bakes `ENV PAYMENTS_API_KEY=FAKE-PAYMENTS-KEY-DO-NOT-USE-0000` into a layer. `package.json` has no dependencies.

PASS if the Dockerfile pins the base image by an exact tag or a digest (not `latest`), sets a non-root `USER`, copies only the runtime files instead of the whole context, and contains no secret value (the key arrives at runtime via env or a mounted file). It is multi-stage, or it is one stage and the reply says why (no build step, no dependencies).
FAIL if `latest` stays, the process still runs as root, `COPY . .` stays, the key value stays in any `ENV`, `ARG` or `RUN`, or the file is unchanged.
