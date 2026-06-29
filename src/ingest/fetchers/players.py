from nba_api.stats.static import players as nba_players


def _inches_to_cm(height_str: str | None) -> float | None:
    if not height_str:
        return None
    try:
        feet, inches = height_str.split("-")
        return round((int(feet) * 12 + int(inches)) * 2.54, 1)
    except (ValueError, AttributeError):
        return None


def _lbs_to_kg(weight: str | int | None) -> float | None:
    if weight is None:
        return None
    try:
        return round(float(weight) * 0.453592, 1)
    except (ValueError, TypeError):
        return None


def fetch_players() -> list[dict]:
    raw = nba_players.get_players()
    return [
        {
            "player_id": p["id"],
            "full_name": p["full_name"],
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "position": None,
            "height_cm": None,
            "weight_kg": None,
            "birth_date": None,
            "country": None,
            "draft_year": None,
            "draft_round": None,
            "draft_number": None,
            "is_active": p["is_active"],
        }
        for p in raw
    ]
