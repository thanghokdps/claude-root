# Sandbox image for running agent-generated code.
#
#   docker build -t evalkit-sandbox .
#
# Every solver command and every pytest invocation runs in a throwaway container
# from this image, with `--network none`. pytest must be baked in: the container
# has no egress, so it cannot pip-install anything at run time.
FROM python:3.11-slim

RUN pip install --no-cache-dir pytest>=7.0 \
 && useradd --create-home --uid 1000 evaluser

# Generated code runs as a non-root user against a bind-mounted /work.
USER evaluser
WORKDIR /work

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
