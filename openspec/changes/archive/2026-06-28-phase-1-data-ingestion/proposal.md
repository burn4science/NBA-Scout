## Why

The platform has no data foundation yet. Before any agent, query, or RAG pipeline can operate, the relational layer must exist: a PostgreSQL database seeded with real NBA player data. This change establishes that foundation using the `nba_api` as the sole source of truth for Phase 1 — structured player biographical data, per-season box stats, and advanced metrics (including PER) across the last five seasons.

## What Changes

- New PostgreSQL schema: `teams`, `players`, `seasons`, `player_season_stats` (global shared layer), plus `tenants` and `tenant_players` (multi-tenant access control stub)
- New ingestion pipeline (`src/ingest/`) that fetches from `nba_api` and populates the schema
- `config.toml` for all tunable ingestion parameters (seasons range, rate-limit delay, batch sizes)
- `.env.example` defining all required environment variables (DB connection string)
- Docker Compose service for PostgreSQL with `pgvector` extension enabled (scoped to dev; prod via Portainer Stack)
- Loguru-based structured logging throughout the pipeline

## Capabilities

### New Capabilities

- `data-ingestion`: nba_api fetch pipeline — teams, players, per-season box stats, per-season advanced stats — written to PostgreSQL across the last 5 seasons (2020-21 through 2024-25)
- `database-schema`: PostgreSQL schema definition for the global relational layer and multi-tenant access control stub, with pgvector extension enabled

### Modified Capabilities

<!-- None — this is a greenfield change. -->

## Impact

- **New dependencies**: `nba_api`, `sqlalchemy`, `psycopg2-binary`, `alembic`, `loguru`, `ruff`, `tomli`
- **New services**: PostgreSQL 16 with `pgvector` extension (Docker Compose)
- **New top-level directory**: `src/ingest/`
- **Config**: `config/config.toml` (seasons, rate limits, batch sizes)
- **Env**: `.env.example` (DB connection URL, optional overrides)
- No existing code is modified — this is purely additive
