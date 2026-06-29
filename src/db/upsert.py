from sqlalchemy import Connection
from sqlalchemy.dialects.postgresql import insert

from db.models import Player, PlayerSeasonStats, Season, Team


def upsert_teams(conn: Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(Team)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["team_id"],
            set_={
                c: insert(Team).excluded[c]
                for c in ("abbreviation", "city", "full_name", "conference", "division")
            },
        )
    )
    result = conn.execute(stmt)
    return result.rowcount


def upsert_players(conn: Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    stmt = (
        insert(Player)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["player_id"],
            set_={
                c: insert(Player).excluded[c]
                for c in (
                    "full_name",
                    "first_name",
                    "last_name",
                    "position",
                    "height_cm",
                    "weight_kg",
                    "birth_date",
                    "country",
                    "draft_year",
                    "draft_round",
                    "draft_number",
                    "is_active",
                )
            },
        )
    )
    result = conn.execute(stmt)
    return result.rowcount


def upsert_seasons(conn: Connection, season_ids: list[str]) -> None:
    """Ensure all season rows exist before inserting stats (FK constraint)."""
    if not season_ids:
        return
    rows = [{"season_id": s} for s in season_ids]
    stmt = insert(Season).values(rows).on_conflict_do_nothing(index_elements=["season_id"])
    conn.execute(stmt)


def upsert_player_season_stats(conn: Connection, rows: list[dict]) -> int:
    if not rows:
        return 0
    stat_cols = [
        "games_played",
        "min_per_game",
        "pts",
        "reb",
        "ast",
        "stl",
        "blk",
        "fg_pct",
        "fg3_pct",
        "ft_pct",
        "per",
        "ts_pct",
        "usg_pct",
        "off_rtg",
        "def_rtg",
    ]
    stmt = (
        insert(PlayerSeasonStats)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["player_id", "team_id", "season_id"],
            set_={c: insert(PlayerSeasonStats).excluded[c] for c in stat_cols},
        )
    )
    result = conn.execute(stmt)
    return result.rowcount
