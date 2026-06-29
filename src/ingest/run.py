from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine

from db.upsert import upsert_player_season_stats, upsert_players, upsert_seasons, upsert_teams
from ingest.config import load_config
from ingest.fetchers.players import fetch_players
from ingest.fetchers.stats import fetch_season_stats
from ingest.fetchers.teams import fetch_teams
from ingest.logger import get_logger
from ingest.retry import with_retry


def main() -> None:
    load_dotenv()
    log = get_logger()

    cfg = load_config()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL is not set. Copy .env.example to .env and configure it.")
        sys.exit(1)

    log.info("NBA Scout ingestion pipeline starting")
    log.info(f"Seasons: {cfg.seasons}")

    engine = create_engine(db_url)

    def _retried(fn):
        return with_retry(
            max_retries=cfg.max_retries,
            delay_seconds=cfg.rate_limit_delay_seconds,
        )(fn)

    _fetch_teams = _retried(fetch_teams)
    _fetch_players = _retried(fetch_players)
    _fetch_season_stats = _retried(fetch_season_stats)

    with engine.begin() as conn:
        log.info("Fetching teams...")
        teams = _fetch_teams()
        if teams:
            n = upsert_teams(conn, teams)
            log.info(f"Upserted {n} team rows")

        log.info("Fetching players...")
        players = _fetch_players()
        if players:
            n = upsert_players(conn, players)
            log.info(f"Upserted {n} player rows")

        upsert_seasons(conn, cfg.seasons)
        log.info(f"Ensured {len(cfg.seasons)} season rows exist")

        total_stat_rows = 0
        for season in cfg.seasons:
            log.info(f"Fetching stats for season {season}...")
            stats = _fetch_season_stats(season)
            if stats:
                # Tag each row with the season_id
                for row in stats:
                    row["season_id"] = season
                n = upsert_player_season_stats(conn, stats)
                log.info(f"  {season}: upserted {n} stat rows for {len(stats)} player-team combos")
                total_stat_rows += n
            else:
                log.warning(f"  {season}: no stats returned — skipping")

    log.info(f"Pipeline complete. Total stat rows upserted: {total_stat_rows}")


if __name__ == "__main__":
    main()
