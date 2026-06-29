"""
Smoke tests — require a running PostgreSQL instance with the schema migrated
and the ingestion pipeline already executed.

Run after:
  docker compose up -d db
  uv run alembic upgrade head
  uv run python -m ingest.run
"""

import os

import pytest
from sqlalchemy import create_engine, text


@pytest.fixture(scope="module")
def engine():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set — skipping smoke tests")
    return create_engine(url)


def test_teams_has_30_rows(engine) -> None:
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM teams")).scalar()
    assert count == 30, f"Expected 30 teams, got {count}"


def test_advanced_stats_not_all_null(engine) -> None:
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM player_season_stats WHERE per IS NOT NULL")
        ).scalar()
    assert count > 0, "No rows with per IS NOT NULL — advanced stats merge may have failed"


def test_pipeline_is_idempotent(engine) -> None:
    with engine.connect() as conn:
        before = conn.execute(text("SELECT COUNT(*) FROM player_season_stats")).scalar()

    from ingest.run import main

    main()

    with engine.connect() as conn:
        after = conn.execute(text("SELECT COUNT(*) FROM player_season_stats")).scalar()

    assert before == after, (
        f"Row count changed after re-run: {before} → {after} (duplicate rows inserted)"
    )
