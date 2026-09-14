# ============================================================
# MT5 AI/ML Trading Bot - Enterprise Edition
# Dockerfile (Python 3.12 slim, multi-stage build, uv-locked)
# Supporting linux/amd64 and linux/arm64
#
# Dependency policy: pyproject.toml + uv.lock are the ONLY build
# source of truth. requirements*.txt are legacy reference files
# and are intentionally NOT used by this build.
# ============================================================

# --- Stage 1: builder ------------------------------------------
FROM python:3.12-slim AS builder

ARG TARGETARCH
WORKDIR /app

# System dependencies for building TA-Lib and Python packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ make \
    libpq-dev \
    wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build TA-Lib C library from source (required by the TA-Lib Python binding)
RUN wget -q https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib-0.6.4-src.tar.gz && \
    tar xf ta-lib-0.6.4-src.tar.gz && \
    cd ta-lib-0.6.4 && ./configure --prefix=/usr && make -j$(nproc) && make install

# Install uv (pinned version, no architecture-specific rewrites needed:
# the pytorch-cpu index in pyproject.toml [tool.uv] handles CPU-only torch
# on both amd64 and arm64)
COPY --from=ghcr.io/astral-sh/uv:0.12.13 /uv /usr/local/bin/uv

# Copy dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Install the locked dependency set (core + ctrader + research + ta-lib;
# no dev tooling in the image, no legacy MT5). --locked fails the build if
# pyproject.toml and uv.lock are out of sync.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --extra ctrader --extra research --extra ta-lib

# --- Stage 2: runtime ------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system dependencies
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy TA-Lib shared libraries from builder (needed by the TA-Lib binding)
COPY --from=builder /usr/lib/libta_lib* /usr/lib/
RUN ldconfig

# Copy the uv-managed virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source and assets
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY main.py .
COPY alembic.ini .

# Setup non-root user for production security
RUN useradd -m -u 1000 trader

# Create log directory and ensure correct ownership
RUN mkdir -p /app/logs && \
    chown -R trader:trader /app && \
    chmod 755 /app/logs

USER trader

# Expose ports for Prometheus (8000) and Dash (8050)
EXPOSE 8000 8050

# Health check to ensure the application environment is sane
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import src.core.config; print('healthy')" || exit 1

# Default execution entrypoint
ENTRYPOINT ["python", "main.py"]
CMD ["--mode", "demo", "--algo", "ensemble"]
