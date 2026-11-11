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
OUTPUTS = ROOT / "outputs"

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

RECRUITMENT_FILES = {
    "batter_candidates": "step4b_batter_candidates.csv",
    "bowler_candidates": "step4b_bowler_candidates.csv",
    "batter_classification": "step4c_batter_classification.csv",
    "bowler_classification": "step4c_bowler_classification.csv",
    "squad": "step4c_rr_squad_evidence.csv",
    "external": "step4c_external_candidate_pool.csv",
    "unresolved": "step4c_unresolved_status.csv",
}

RECRUITMENT_REQUIRED_COLUMNS = {
    "batter_candidates": {"context_key", "player_id", "player_name", "team_name", "comp_name", "season", "pressure_events", "baseline_events", "pressure_matches", "baseline_matches", "evidence_label", "pressure_semantics"},
    "bowler_candidates": {"context_key", "player_id", "player_name", "team_name", "comp_name", "season", "pressure_legal_balls", "baseline_legal_balls", "pressure_matches", "baseline_matches", "candidate_dismissal_events", "candidate_dismissal_matches", "evidence_label", "pressure_semantics"},
    "batter_classification": {"context_key", "player_id", "player_name", "classification", "rr_reference_season_matches", "auction_availability_status", "all_supplied_mapping_contexts"},
    "bowler_classification": {"context_key", "player_id", "player_name", "classification", "rr_reference_season_matches", "auction_availability_status", "all_supplied_mapping_contexts"},
    "squad": {"player_id", "player_name", "season", "matches_represented", "role", "auction_availability_status", "evidence_confidence"},
    "external": {"role", "player_id", "player_name", "historical_context_count", "historical_contexts", "auction_availability_status"},
    "unresolved": {"classification_key"},
}


def _read_csv(name: str, required: bool = True) -> pd.DataFrame:
    path = RAW / name
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required data file is missing: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def _read_recruitment_csv(key: str) -> pd.DataFrame:
    path = OUTPUTS / RECRUITMENT_FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"Recruitment evidence file is missing: {path}")
    frame = pd.read_csv(path, low_memory=False)
    missing = sorted(RECRUITMENT_REQUIRED_COLUMNS[key].difference(frame.columns))
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")
    if frame.duplicated().any():
        raise ValueError(f"{path.name} contains duplicate rows.")
    if key != "unresolved" and frame.empty:
        raise ValueError(f"{path.name} is unexpectedly empty.")
    return frame.fillna("")


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


def get_venues() -> list[dict]:
    matches = _data()["matches"]
    return (
        matches.groupby(["venue_id", "venue_country"], as_index=False)
        .agg(match_count=("match_id", "nunique"))
        .sort_values(["venue_country", "venue_id"])
        .to_dict("records")
    )


def get_shot_data(venue_id: str | None = None) -> dict:
    ball = _data()["ball"]
    matches = _data()["matches"]
    competitions = _data()["competitions"]
    selected_venue = None
    if venue_id and str(venue_id).isdigit():
        selected_venue = int(venue_id)
        match_ids = matches.loc[matches["venue_id"].eq(selected_venue), "match_id"]
        ball = ball[ball["match_id"].isin(match_ids)]
    venue_matches = matches[matches["venue_id"].eq(selected_venue)] if selected_venue is not None else matches.iloc[0:0]
    venue_matches = venue_matches.merge(
        competitions[["comp_id", "comp_name", "match_format", "season"]],
        on="comp_id", how="left", validate="many_to_one",
    )
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
        "venue_id": selected_venue,
        "venue_country": (
            str(venue_matches["venue_country"].iloc[0])
            if not venue_matches.empty else None
        ),
        "venue_count": int(len(venue_matches)),
        "formats": sorted(venue_matches["match_format"].dropna().astype(str).unique().tolist()),
        "seasons": sorted(venue_matches["season"].dropna().astype(str).unique().tolist()),
        "matches": venue_matches[
            ["match_date", "home_team", "away_team", "comp_name", "match_format", "result"]
        ].sort_values("match_date", ascending=False).to_dict("records") if selected_venue is not None else [],
    }


@lru_cache(maxsize=1)
def get_recruitment_data() -> dict:
    evidence = {key: _read_recruitment_csv(key) for key in RECRUITMENT_FILES}
    batter = evidence["batter_candidates"].merge(
        evidence["batter_classification"][
            [
                "context_key", "classification", "rr_reference_season_matches",
                "rr_reference_contexts", "all_supplied_mapping_contexts",
                "evidence_confidence", "auction_availability_status",
            ]
        ],
        on="context_key", how="left", validate="one_to_one",
    )
    bowler = evidence["bowler_candidates"].merge(
        evidence["bowler_classification"][
            [
                "context_key", "classification", "rr_reference_season_matches",
                "rr_reference_contexts", "all_supplied_mapping_contexts",
                "evidence_confidence", "auction_availability_status",
            ]
        ],
        on="context_key", how="left", validate="one_to_one",
    )
    candidates = pd.concat([batter, bowler], ignore_index=True, sort=False).fillna("")
    candidates["candidate_key"] = (
        candidates["role"].astype(str) + ":" + candidates["context_key"].astype(str)
    )
    if candidates["classification"].eq("").any():
        raise ValueError("A candidate is missing its Step 4C classification.")
    if candidates["candidate_key"].duplicated().any():
        raise ValueError("Recruitment candidates are duplicated at role/context grain.")

    data = _data()
    competitions = data["competitions"]
    matches = data["matches"].merge(
        competitions[["comp_id", "season"]],
        on="comp_id", how="left", validate="many_to_one",
    )
    reference_season = str(evidence["squad"]["season"].astype(str).iloc[0])
    rr_matches = matches[
        (matches["home_team_id"].eq(3) | matches["away_team_id"].eq(3))
        & matches["season"].astype(str).eq(reference_season)
    ]["match_id"].nunique()

    def records(frame: pd.DataFrame) -> list[dict]:
        return frame.to_dict("records")

    classification_counts = candidates["classification"].value_counts().to_dict()
    return {
        "overview": {
            "reference_season": reference_season,
            "rr_team_id": 3,
            "rr_matches": int(rr_matches),
            "rr_participants": int(evidence["squad"]["player_id"].nunique()),
            "candidate_contexts": len(candidates),
            "rr_candidate_contexts": int(candidates["classification"].eq("RR_REFERENCE_SEASON_PARTICIPANT").sum()),
            "external_candidate_contexts": int(candidates["classification"].eq("EXTERNAL_HISTORICAL_CANDIDATE").sum()),
            "external_unique_players": int(evidence["external"]["player_id"].nunique()),
            "unresolved_contexts": int(candidates["classification"].eq("STATUS_UNRESOLVED").sum()),
            "classification_counts": classification_counts,
        },
        "candidates": records(candidates.sort_values(["classification", "role", "player_name", "context_key"])),
        "squad": records(evidence["squad"].sort_values(["player_name", "player_id"])),
        "external": records(evidence["external"].sort_values(["role", "player_name"])),
        "limitations": [
            "Historical team context is not proof of 2027 auction availability.",
            "IPL 2026 is the latest supplied RR reference season, not confirmation of the 2027 squad.",
            "Roles are not verified for recruitment planning.",
            "Retention, release, auction-pool, budget, overseas-slot, and squad-need fields are not supplied.",
            "Bowler economy and conceded runs remain unavailable.",
            "chase_baseline is an inferred chase-context proxy, not measured psychological pressure.",
        ],
    }
