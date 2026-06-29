## 1. Project Scaffolding

- [x] 1.1 Initialise `uv` project: create `pyproject.toml` with `[project]`, `[tool.ruff]`, and `[tool.loguru]` sections
- [x] 1.2 Add runtime dependencies: `nba_api`, `sqlalchemy`, `psycopg2-binary`, `alembic`, `loguru`, `tomli`
- [x] 1.3 Add dev dependencies: `ruff`, `pytest`, `pytest-postgresql`
- [x] 1.4 Create top-level directory structure: `src/ingest/`, `src/db/`, `alembic/`
- [x] 1.5 Create `config/config.toml` with `seasons`, `rate_limit_delay_seconds`, `max_retries`, `batch_size`
- [x] 1.6 Create `.env.example` with `DATABASE_URL` and `HOST_SHARED_DATA_DIR` placeholders
- [x] 1.7 Create `src/ingest/logger.py` — loguru setup with console sink and rotating file sink; imported once and reused across all modules

## 2. Docker Compose & Database Bootstrap

- [x] 2.1 Create `docker-compose.yml` with a `db` service using `pgvector/pgvector:pg16` image; bind data volume via `${HOST_SHARED_DATA_DIR}`
- [x] 2.2 Verify `pgvector` extension is available in the running container (`SELECT * FROM pg_extension WHERE extname = 'pgvector'`)
- [x] 2.3 Configure Alembic: run `uv run alembic init alembic`, update `env.py` to read `DATABASE_URL` from `.env` and use SQLAlchemy ORM `target_metadata`

## 3. Database Schema (ORM Models + Migration)

- [x] 3.1 Create `src/db/models.py` — define `Team`, `Player`, `Season`, `PlayerSeasonStats`, `Tenant`, `TenantPlayer` ORM models matching the database-schema spec
- [x] 3.2 Enable `pgvector` extension in the initial Alembic migration using `op.execute("CREATE EXTENSION IF NOT EXISTS vector")`
- [x] 3.3 Generate initial Alembic migration: `uv run alembic revision --autogenerate -m "initial schema"`
- [x] 3.4 Verify migration applies cleanly on a fresh database: `uv run alembic upgrade head`
- [x] 3.5 Verify rollback works cleanly: `uv run alembic downgrade base`

## 4. Config Loader

- [x] 4.1 Create `src/ingest/config.py` — load and validate `config/config.toml` using `tomli`; raise `ConfigurationError` with a descriptive message for any missing required key
- [x] 4.2 Write unit tests for `ConfigurationError` on missing keys

## 5. nba_api Fetch Layer

- [x] 5.1 Create `src/ingest/fetchers/teams.py` — fetch all teams via `nba_api.static.teams.get_teams()`; return list of dicts matching `Team` model fields
- [x] 5.2 Create `src/ingest/fetchers/players.py` — fetch all players via `nba_api.static.players.get_players()`; return list of dicts matching `Player` model fields
- [x] 5.3 Create `src/ingest/fetchers/stats.py` — fetch `LeagueDashPlayerStats` (box) and `LeagueDashPlayerStats` advanced per season; merge on `(PLAYER_ID, TEAM_ID)` into a flat dict per row
- [x] 5.4 Create `src/ingest/retry.py` — exponential backoff decorator using `max_retries` and `rate_limit_delay_seconds` from config; logs WARNING on retry, ERROR on exhaustion
- [x] 5.5 Apply the retry decorator to all three fetcher functions

## 6. Database Write Layer

- [x] 6.1 Create `src/db/upsert.py` — implement `upsert_teams()`, `upsert_players()`, `upsert_seasons()`, `upsert_player_season_stats()` using SQLAlchemy Core `insert().on_conflict_do_update()`
- [x] 6.2 Ensure `upsert_seasons()` inserts season strings before `upsert_player_season_stats()` to satisfy the FK constraint

## 7. Pipeline Orchestrator

- [x] 7.1 Create `src/ingest/run.py` — main entrypoint; orchestrates: load config → init DB session → upsert teams → upsert players → for each season: fetch stats → upsert stats; log INFO summary at start and end
- [x] 7.2 Confirm the pipeline can be invoked with `uv run python -m ingest.run`
- [x] 7.3 Run the full pipeline against the live database; verify row counts in `teams`, `players`, `player_season_stats` via `psql` queries

## 8. Validation & Smoke Tests

- [x] 8.1 Write a smoke test that asserts `teams` has exactly 30 rows after ingestion
- [x] 8.2 Write a smoke test that asserts `player_season_stats` has at least one row with `per IS NOT NULL` (confirms advanced stats merged correctly)
- [x] 8.3 Write a smoke test that asserts re-running the pipeline produces no duplicate rows (idempotency check via COUNT before and after second run)
- [x] 8.4 Run `uv run ruff check src/` and `uv run ruff format --check src/` — fix any violations
