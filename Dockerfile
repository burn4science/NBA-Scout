FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first — this layer is cached until pyproject.toml / uv.lock changes.
# --extra chunking pulls the heavy Docling/torch stack so the image is fully
# self-contained and runs on the homelab without any host-side dependency.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --extra chunking

# Copy source and config after deps so source changes don't bust the dep cache.
# config/ MUST be baked in — the running container has no access to the dev host.
COPY src/ ./src/
COPY config/ ./config/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Install the project itself into the venv
RUN uv sync --frozen --no-dev --extra chunking && \
    mkdir -p /app/logs && \
    useradd -r -u 1001 -m app && \
    chown -R app:app /app

USER app

CMD ["uv", "run", "python", "-m", "ingest.run"]
