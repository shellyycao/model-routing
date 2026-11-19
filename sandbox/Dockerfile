# Sandbox image for executing UNTRUSTED model-generated cleaning/analysis code.
# Build:  docker build -t model-routing-xai-sandbox:1.0 sandbox/
#
# Isolation is enforced at `docker run` time by src/workflow/executor.py (no network, read-only
# root fs, tmpfs /tmp, memory/CPU/pids limits, cap-drop ALL, no-new-privileges, non-root user,
# read-only inputs, only /sandbox/output writable, no host env or credentials).
# The image itself only provides a pinned interpreter + libraries and a non-root user.
#
# Pinning: the base image is pinned by tag. For full provenance also pin the digest
# (python:3.12.8-slim-bookworm@sha256:...) once it has been pulled and recorded; the executor
# records the local image ID in ExecutionResult.sandbox_image for every run.
FROM python:3.12.8-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/tmp \
    MPLCONFIGDIR=/tmp

RUN pip install --no-cache-dir numpy==2.2.6 pandas==2.2.3 \
 && groupadd --gid 10001 sandbox \
 && useradd --uid 10001 --gid 10001 --no-create-home --home-dir /tmp --shell /usr/sbin/nologin sandbox \
 && mkdir -p /sandbox/input /sandbox/code /sandbox/output \
 && chown 10001:10001 /sandbox/output

USER 10001:10001
WORKDIR /sandbox/output
ENTRYPOINT ["python", "-I", "-B"]
