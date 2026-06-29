## Context

The platform has no running code yet. This is the first change — it establishes the PostgreSQL schema and the `nba_api` ingestion pipeline that all subsequent phases depend on. The environment spec constrains us to Docker Compose locally and a Portainer Stack in production, with all physical paths injected via `${HOST_SHARED_DATA_DIR}`. No Docling, no vector index, no LLM in this change.

## Goals / Non-Goals

**Goals:**
- Define and migrate the complete global relational schema (teams, players, seasons, player_season_stats)
- Stub the multi-tenant access control tables (tenants, tenant_players) — schema only, no enforcement logic yet
- Implement an idempotent ingestion pipeline that fetches 5 seasons from `nba_api` and upserts into the schema
- Enable `pgvector` extension on the database (no indices yet — prepares for Phase 2)
- Follow all project conventions: `uv`, `loguru`, `ruff`, `config.toml`, `.env`

**Non-Goals:**
- Salary data, free agency flags, or contract details (no source for these in nba_api)
- Vector embeddings or HNSW indices (Phase 2)
- Tenant isolation enforcement (Phase 3)
- LangGraph tooling, FastAPI, or any LLM component
- Kaggle CSV ingestion (later change)
- Async ingestion (nba_api is synchronous; complexity not warranted here)

## Decisions

### D1 — SQLAlchemy ORM for models, Core for bulk inserts

Use SQLAlchemy ORM (`declarative_base`) to define models — clean, readable, Alembic-compatible. Use SQLAlchemy Core `insert().on_conflict_do_update()` for bulk upserts during ingestion — avoids session-level overhead on thousands of rows.

**Alternative considered:** pure `psycopg2` with raw SQL. Rejected — loses Alembic integration and type safety on schema definition.

### D2 — Alembic for all schema migrations

Schema changes go through Alembic from day 1. The `env.py` autogenerates from ORM models. This is non-negotiable for Portainer production deployments where we cannot drop and recreate.

**Alternative considered:** `CREATE TABLE IF NOT EXISTS` in an init script. Rejected — not evolvable, breaks on schema changes without drop.

### D3 — Single `player_season_stats` table (box + advanced merged)

Fetch `leaguedashplayerstats` (box stats) and `leaguedashplayeradvanced` (PER, TS%, USG%, etc.) separately per season, then merge on `(player_id, team_id, season_id)` before upsert into one wide table.

**Alternative considered:** two separate tables (`player_box_stats`, `player_advanced_stats`). Rejected — makes the SQL tool layer's queries more complex without benefit. A single flat row per player-season is what the agent tools need.

### D4 — Upsert strategy (idempotent full-season refresh)

On conflict `(player_id, team_id, season_id)`, update all stat columns. This means re-running the pipeline for any season is safe and self-healing (nba_api retroactively corrects box scores).

**Alternative considered:** delete-and-reinsert per season. Rejected — creates a window where the table is partially empty, bad for concurrent reads.

### D5 — Rate limiting via configurable sleep

`nba_api` is an unofficial API. Calls are throttled at the data.nba.com level. A configurable `rate_limit_delay_seconds` (default: `0.6`) is inserted between every API call. An exponential backoff with 3 retries handles transient 429s.

**Alternative considered:** a semaphore-based async approach. Rejected — `nba_api` is synchronous; async wrapper adds complexity for no throughput gain.

### D6 — Season range in config.toml

`seasons = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25"]` as an explicit list in `config.toml`. Explicit list (not a derived range) makes it easy to add/remove seasons without arithmetic.

## Risks / Trade-offs

- **nba_api availability** → It's an unofficial API; it has no SLA. The pipeline must handle timeouts and HTTP errors gracefully without crashing. Mitigation: retry with backoff, log failures per-season, continue to next season.
- **Advanced stats endpoint coverage** → Some advanced stats endpoints may return incomplete data for the oldest seasons. Mitigation: merge on a LEFT JOIN basis — missing advanced cols default to `NULL`, not an error.
- **Schema evolution debt** → As Docling and vector layers are added in Phase 2, the schema will grow. Mitigation: Alembic from day 1 makes this mechanical.
- **Portainer volume binding** → `${HOST_SHARED_DATA_DIR}` must be set in `.env` for both dev and prod. If unset, Docker Compose will fail to start. Mitigation: validate env var presence in a startup check; document clearly in `.env.example`.

## Migration Plan

1. `docker compose up -d db` — starts PostgreSQL with pgvector
2. `uv run alembic upgrade head` — applies all migrations
3. `uv run python -m ingest.run` — executes the ingestion pipeline
4. Rollback: `uv run alembic downgrade base` drops all tables (data loss acceptable — pipeline is re-runnable)
