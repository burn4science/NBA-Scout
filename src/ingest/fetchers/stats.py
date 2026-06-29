from nba_api.stats.endpoints import leaguedashplayerstats


def fetch_season_stats(season: str) -> list[dict]:
    """Fetch box + advanced stats for all players in a season, merged into flat dicts."""
    box = _fetch_box(season)
    advanced = _fetch_advanced(season)

    # Index advanced by (player_id, team_id) for O(1) merge
    adv_index = {(r["player_id"], r["team_id"]): r for r in advanced}

    merged = []
    for row in box:
        key = (row["player_id"], row["team_id"])
        adv = adv_index.get(key, {})
        adv_fields = {k: adv.get(k) for k in ("per", "ts_pct", "usg_pct", "off_rtg", "def_rtg")}
        merged.append({**row, **adv_fields})
    return merged


def _fetch_box(season: str) -> list[dict]:
    response = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        per_mode_detailed="PerGame",
        measure_type_detailed_defense="Base",
    )
    df = response.get_data_frames()[0]
    rows = []
    for _, r in df.iterrows():
        rows.append(
            {
                "player_id": int(r["PLAYER_ID"]),
                "team_id": int(r["TEAM_ID"]),
                "games_played": _safe_int(r.get("GP")),
                "min_per_game": _safe_float(r.get("MIN")),
                "pts": _safe_float(r.get("PTS")),
                "reb": _safe_float(r.get("REB")),
                "ast": _safe_float(r.get("AST")),
                "stl": _safe_float(r.get("STL")),
                "blk": _safe_float(r.get("BLK")),
                "fg_pct": _safe_float(r.get("FG_PCT")),
                "fg3_pct": _safe_float(r.get("FG3_PCT")),
                "ft_pct": _safe_float(r.get("FT_PCT")),
            }
        )
    return rows


def _fetch_advanced(season: str) -> list[dict]:
    try:
        response = leaguedashplayerstats.LeagueDashPlayerStats(
            season=season,
            per_mode_detailed="PerGame",
            measure_type_detailed_defense="Advanced",
        )
        df = response.get_data_frames()[0]
        rows = []
        for _, r in df.iterrows():
            rows.append(
                {
                    "player_id": int(r["PLAYER_ID"]),
                    "team_id": int(r["TEAM_ID"]),
                    # nba_api advanced endpoint exposes PIE; true PER requires a separate endpoint
                    "per": _safe_float(r.get("PIE")),
                    "ts_pct": _safe_float(r.get("TS_PCT")),
                    "usg_pct": _safe_float(r.get("USG_PCT")),
                    "off_rtg": _safe_float(r.get("OFF_RATING")),
                    "def_rtg": _safe_float(r.get("DEF_RATING")),
                }
            )
        return rows
    except Exception:
        return []


def _safe_float(val) -> float | None:
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> int | None:
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None
