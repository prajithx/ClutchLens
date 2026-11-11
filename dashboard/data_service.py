"""Safe, cached access to the supplied ClutchLens data.

The service deliberately exposes descriptive conditional metrics only. It
does not calculate pressure ratings, rankings, economy, or conceded runs.
"""

from functools import lru_cache
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

TRUSTED_METRICS = {
    "source_counts": "verified audit inventory",
    "conditional_batter_runs": "strict null-extra, zero-secondary-field rows",
    "boundary_flags": "source is_four/is_six fields, descriptive only",
    "legal_ball_count": "exclude wide and Overstep; other remains a caveat",
    "dismissal_events": "reported by dismissal type, not all as bowler wickets",
    "categorical_shots": "stroke and delivery-style distributions; not spatial locations",
}
BLOCKED_METRICS = {
    "pressure_rating": "team totals and target semantics remain under validation",
    "bowler_economy": "bowler-conceded runs are not encoded reliably",
    "player_ranking": "not produced in UI foundation step",
    "shot_coordinates": "source contains no verified spatial coordinates",
}


def _read_csv(name: str, required: bool = True) -> pd.DataFrame:
    path = RAW / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required data file is missing: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


@lru_cache(maxsize=1)
def _data() -> dict[str, pd.DataFrame]:
    ball = _read_csv("ball_by_ball.csv")
    matches = _read_csv("matches.csv")
    competitions = _read_csv("competitions.csv")
    mapping = _read_csv("competition_team_player_mapping.csv")
    return {"ball": ball, "matches": matches, "competitions": competitions, "mapping": mapping}


def get_dashboard_data() -> dict:
    data = _data()
    ball = data["ball"]
    matches = data["matches"]
    competitions = data["competitions"]
    match_meta = matches.merge(
        competitions[["comp_id", "match_format", "season"]],
        on="comp_id",
        how="left",
        validate="many_to_one",
    )
    format_counts = match_meta["match_format"].value_counts().rename_axis("label").reset_index(name="value")
    season_counts = match_meta.groupby("season").size().reset_index(name="value")
    return {
        "counts": [
            {"label": "Delivery rows", "value": f"{len(ball):,}", "detail": "Verified source rows"},
            {"label": "Matches with ball data", "value": f"{ball['match_id'].nunique():,}", "detail": "Distinct match IDs"},
            {"label": "Competitions", "value": f"{competitions['comp_id'].nunique():,}", "detail": "Reference competitions"},
            {"label": "Mapped players", "value": f"{data['mapping']['player_id'].nunique():,}", "detail": "IDs in supplied mapping"},
        ],
        "formats": format_counts.to_dict("records"),
        "seasons": season_counts.to_dict("records"),
        "trusted": TRUSTED_METRICS,
        "blocked": BLOCKED_METRICS,
    }


@lru_cache(maxsize=1)
def get_players() -> list[dict]:
    mapping = _data()["mapping"]
    players = (
        mapping[["player_id", "player_name"]]
        .drop_duplicates()
        .groupby("player_id", as_index=False)
        .agg(name=("player_name", "first"))
        .sort_values("name")
    )
    return players.rename(columns={"player_id": "id"}).to_dict("records")


def get_player_data(player_id: str) -> dict | None:
    if not str(player_id).isdigit():
        return None
    player_id_int = int(player_id)
    data = _data()
    ball = data["ball"]
    mapping = data["mapping"]
    match_rows = ball[
        (ball["striker_id"].eq(player_id_int) | ball["bowler_id"].eq(player_id_int))
        & ball["match_id"].notna()
    ]
    identity = mapping[mapping["player_id"].eq(player_id_int)]
    if identity.empty and match_rows.empty:
        return None
    name = identity["player_name"].iloc[0] if not identity.empty else (
        match_rows["striker_name"].dropna().iloc[0]
        if not match_rows["striker_name"].dropna().empty
        else match_rows["bowler_name"].dropna().iloc[0]
    )
    strict = ball[ball["extras_type"].isna() & ball["extras_2_runs"].eq(0)]
    batting = strict[strict["striker_id"].eq(player_id_int)]
    bowling = ball[ball["bowler_id"].eq(player_id_int)]
    dismissals = ball[ball["dismissed_player_id"].eq(player_id_int)]
    return {
        "id": player_id_int,
        "name": name,
        "competitions": int(identity["comp_id"].nunique()) if not identity.empty else 0,
        "batting": {
            "eligible_deliveries": len(batting),
            "observed_runs": int(batting["runs"].sum()),
            "boundaries": int(batting["is_four"].sum() + batting["is_six"].sum()),
            "matches": int(batting["match_id"].nunique()),
        },
        "bowling": {
            "deliveries": int(bowling["legal_ball"].sum()) if "legal_ball" in bowling else int(
                (~bowling["extras_type"].isin(["wide", "Overstep"])).sum()
            ),
            "matches": int(bowling["match_id"].nunique()),
            "dismissal_events": int(bowling["is_wicket"].sum()),
            "candidate_bowler_wickets": int(
                bowling["dismissal_type"].isin(["Bowled", "Caught", "LBW", "Stump", "Hit Wicket"]).sum()
            ),
        },
        "dismissals": int(len(dismissals)),
        "status": "Descriptive conditional metrics only; no rating or ranking is calculated.",
    }


def get_shot_data() -> dict:
    ball = _data()["ball"]
    strokes = ball["stroke"].fillna("Unspecified").value_counts().head(12)
    delivery_styles = ball["delivery_style"].fillna("Unspecified").value_counts().head(10)
    pace_spin = ball["pace_or_spin"].fillna("Unspecified").value_counts()
    return {
        "strokes": [{"label": str(label), "value": int(value)} for label, value in strokes.items()],
        "delivery_styles": [{"label": str(label), "value": int(value)} for label, value in delivery_styles.items()],
        "pace_spin": [{"label": str(label), "value": int(value)} for label, value in pace_spin.items()],
        "total_rows": len(ball),
        "missing_stroke": int(ball["stroke"].isna().sum()),
        "missing_delivery_style": int(ball["delivery_style"].isna().sum()),
    }
