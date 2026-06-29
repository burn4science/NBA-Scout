FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Install dependencies first — this layer is cached until pyproject.toml / uv.lock changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source after deps so source changes don't bust the dep cache
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Install the project itself into the venv
RUN uv sync --frozen --no-dev && \
    mkdir -p /app/logs && \
    useradd -r -u 1001 -m app && \
    chown -R app:app /app

USER app

CMD ["uv", "run", "python", "-m", "ingest.run"]
