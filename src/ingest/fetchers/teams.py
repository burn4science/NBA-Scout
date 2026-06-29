from nba_api.stats.static import teams as nba_teams


def fetch_teams() -> list[dict]:
    raw = nba_teams.get_teams()
    return [
        {
            "team_id": t["id"],
            "abbreviation": t["abbreviation"],
            "city": t["city"],
            "full_name": t["full_name"],
            "conference": None,
            "division": None,
        }
        for t in raw
    ]
