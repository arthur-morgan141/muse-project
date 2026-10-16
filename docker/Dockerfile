# ==============================================================================
# Production Dockerfile for Meta Muse Project
# Multi-stage build for minimal image footprint and hardened runtime
# ==============================================================================

# Stage 1: Build & wheels generator
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels .

# Stage 2: Minimal Production Image
FROM python:3.12-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MUSE_ENV=production

WORKDIR /app

# Non-root user setup for security
RUN groupadd -g 1001 musegroup && \
    useradd -u 1001 -g musegroup -s /bin/bash -m museuser

COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

# Copy configuration and project structure
COPY config/ /app/config/
COPY scripts/ /app/scripts/

# Create runtime session directories with proper permissions
RUN mkdir -p /app/data/sessions && \
    chown -R museuser:musegroup /app

USER museuser

ENTRYPOINT ["muse"]
CMD ["--help"]
