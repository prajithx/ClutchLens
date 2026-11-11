"""Build the Step 4C Rajasthan Royals recruitment-relevance audit.

This audit classifies Step 4B contexts against the latest supplied RR
reference-season participation evidence. It does not infer 2027 auction
availability, squad needs, roles, retention, release, or target status.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"

RR_TEAM_ID = 3
AUCTION_STATUS = "NOT_VERIFIED_FROM_SUPPLIED_DATA"
RAW_FILES = [
    "teams.csv",
    "competitions.csv",
    "matches.csv",
    "playing_eleven.csv",
    "competition_team_player_mapping.csv",
]


def read_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")
    return pd.read_csv(path, low_memory=False)


def validate_schema(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {', '.join(missing)}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def establish_reference(
    teams: pd.DataFrame, competitions: pd.DataFrame, matches: pd.DataFrame
) -> tuple[int, pd.DataFrame]:
    rr_contexts = teams[teams["team_id"].eq(RR_TEAM_ID)].merge(
        competitions, on="comp_id", how="left", validate="many_to_one"
    )
    if rr_contexts[["comp_name", "season", "match_format"]].isna().any().any():
        raise ValueError("RR team contexts could not be mapped to competitions.")
    relevant = matches[
        matches["home_team_id"].eq(RR_TEAM_ID)
        | matches["away_team_id"].eq(RR_TEAM_ID)
    ][["match_id", "comp_id"]].merge(
        competitions[["comp_id", "comp_name", "match_format", "season"]],
        on="comp_id",
        how="left",
        validate="many_to_one",
    )
    seasons = pd.to_numeric(relevant["season"], errors="coerce").dropna()
    if seasons.empty:
        raise ValueError("No numeric RR season is present in supplied match metadata.")
    reference_season = int(seasons.max())
    reference_matches = relevant[
        pd.to_numeric(relevant["season"], errors="coerce").eq(reference_season)
    ].copy()
    if reference_matches.empty:
        raise ValueError("No RR matches found for the selected reference season.")
    return reference_season, reference_matches


def build_squad_evidence(
    reference_season: int,
    reference_matches: pd.DataFrame,
    playing_eleven: pd.DataFrame,
    mapping: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    played = playing_eleven[
        playing_eleven["match_id"].isin(reference_matches["match_id"])
        & playing_eleven["team_id"].eq(RR_TEAM_ID)
        & playing_eleven["is_played"].eq(True)
    ].merge(
        reference_matches,
        on="match_id",
        how="left",
        validate="many_to_one",
    )
    identity = mapping[
        ["comp_id", "team_id", "player_id", "player_name"]
    ].drop_duplicates()
    if identity.duplicated(["comp_id", "team_id", "player_id"]).any():
        raise ValueError("RR mapping has duplicate contextual identity rows.")
    played = played.merge(
        identity,
        on=["comp_id", "team_id", "player_id"],
        how="left",
        validate="many_to_one",
    )
    if played["player_name"].isna().any():
        raise ValueError("Played RR rows contain unmapped player identities.")
    if played.duplicated(["match_id", "team_id", "player_id"]).any():
        raise ValueError("Playing-XI evidence contains duplicate player-match rows.")

    squad = (
        played.groupby(
            ["comp_id", "comp_name", "match_format", "season", "team_id", "player_id", "player_name"],
            dropna=False,
        )
        .agg(
            matches_represented=("match_id", "nunique"),
            playing_eleven_rows=("match_id", "size"),
            captain_matches=("is_captain", "sum"),
            wicketkeeper_matches=("is_wk", "sum"),
            impact_matches=("is_impact", "sum"),
        )
        .reset_index()
    )
    squad["role"] = "UNKNOWN_NOT_INFERRED"
    squad["evidence_source"] = (
        "playing_eleven.is_played joined to matches and contextual player mapping"
    )
    squad["evidence_confidence"] = "HIGH_FOR_SUPPLIED_PARTICIPATION"
    squad["auction_availability_status"] = AUCTION_STATUS
    squad["reference_season"] = reference_season
    squad["grain"] = "one row per supplied RR reference-season comp/team/player context"
    return squad, played


def mapping_name_audit(mapping: pd.DataFrame) -> pd.DataFrame:
    names = (
        mapping.dropna(subset=["player_id", "player_name"])
        .groupby("player_id")["player_name"]
        .agg(lambda values: sorted(set(values.astype(str))))
    )
    conflicts = names[names.map(len).gt(1)]
    return pd.DataFrame(
        [
            {
                "player_id_name_conflicts": len(conflicts),
                "mapping_player_ids_checked": len(names),
                "identity_rule": "same supplied player_id is consolidated only when supplied names are consistent",
                "evidence_confidence": "HIGH" if conflicts.empty else "LOW",
            }
        ]
    )


def classify_candidates(
    candidate: pd.DataFrame,
    role: str,
    reference_players: pd.DataFrame,
    mapping: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    source = candidate.copy()
    source["role"] = role
    source["source_candidate_context_key"] = source["context_key"]
    reference = reference_players.groupby("player_id", as_index=False).agg(
        rr_reference_season_matches=("match_id", "nunique"),
        rr_reference_contexts=("context_key", lambda values: ";".join(sorted(set(values)))),
    )
    source = source.merge(reference, on="player_id", how="left", validate="many_to_one")
    source["classification"] = source["rr_reference_season_matches"].notna().map(
        {
            True: "RR_REFERENCE_SEASON_PARTICIPANT",
            False: "EXTERNAL_HISTORICAL_CANDIDATE",
        }
    )
    source["rr_reference_season_matches"] = source[
        "rr_reference_season_matches"
    ].fillna(0).astype(int)
    source["rr_reference_contexts"] = source["rr_reference_contexts"].fillna(
        "NONE_IN_SELECTED_REFERENCE_SEASON"
    )
    source["evidence_source"] = (
        "Step 4B candidate context plus supplied RR reference-season playing_eleven "
        "and competition/team/player mapping"
    )
    source["evidence_confidence"] = "HIGH_FOR_CLASSIFICATION"
    source["auction_availability_status"] = AUCTION_STATUS
    source["role_basis"] = "Step 4B candidate category; no new role inference"
    source["grain"] = "one row per Step 4B candidate contextual identity"

    identity_contexts = (
        mapping.groupby("player_id")
        .apply(
            lambda group: ";".join(
                f"{int(row.comp_id)}:{int(row.team_id)}:{row.player_name}"
                for row in group[["comp_id", "team_id", "player_name"]]
                .drop_duplicates()
                .sort_values(["comp_id", "team_id"])
                .itertuples(index=False)
            ),
            include_groups=False,
        )
        .rename("all_supplied_mapping_contexts")
    )
    source = source.merge(identity_contexts, on="player_id", how="left", validate="many_to_one")
    if source["all_supplied_mapping_contexts"].isna().any():
        source["classification"] = "STATUS_UNRESOLVED"
        source["evidence_confidence"] = "LOW_UNMAPPED_IDENTITY"

    classification_columns = [
        "selection_order", "role", "context_key", "source_candidate_context_key",
        "player_id", "player_name", "team_id", "team_name", "comp_id", "comp_name",
        "match_format", "season", "classification", "rr_reference_season_matches",
        "rr_reference_contexts", "all_supplied_mapping_contexts", "evidence_source",
        "evidence_confidence", "auction_availability_status", "role_basis", "grain",
    ]
    classifications = source[classification_columns].copy()
    classifications["classification_key"] = (
        classifications["role"] + ":" + classifications["context_key"]
    )
    external = classifications[
        classifications["classification"].eq("EXTERNAL_HISTORICAL_CANDIDATE")
    ].copy()
    external = (
        external.groupby(["role", "player_id", "player_name"], as_index=False)
        .agg(
            historical_context_count=("context_key", "nunique"),
            historical_contexts=("context_key", lambda values: ";".join(sorted(set(values)))),
            historical_teams=("team_name", lambda values: ";".join(sorted(set(values)))),
            historical_competitions=("comp_name", lambda values: ";".join(sorted(set(values)))),
            latest_candidate_context_season=("season", "max"),
            evidence_source=("evidence_source", "first"),
            evidence_confidence=("evidence_confidence", "first"),
            auction_availability_status=("auction_availability_status", "first"),
        )
    )
    external["classification"] = "EXTERNAL_HISTORICAL_CANDIDATE"
    external["grain"] = "one row per unique supplied player_id and Step 4B role"
    external["availability_note"] = (
        "Non-RR historical evidence does not establish 2027 auction availability."
    )
    unresolved = classifications[
        classifications["classification"].eq("STATUS_UNRESOLVED")
    ].copy()
    unresolved["unresolved_reason"] = "Supplied identity could not be mapped consistently."
    return classifications, external, unresolved


def report(
    reference_season: int,
    reference_matches: pd.DataFrame,
    squad: pd.DataFrame,
    batters: pd.DataFrame,
    bowlers: pd.DataFrame,
    external: pd.DataFrame,
    unresolved: pd.DataFrame,
    identity_audit: pd.DataFrame,
    problem_statement: str | None,
    raw_hashes: dict[str, str],
) -> str:
    lines = [
        "# Step 4C Rajasthan Royals Recruitment Relevance Audit",
        "",
        "## Purpose and challenge context",
        "This report converts Step 4B evidence contexts into an RR reference-season participation audit. It does not produce final auction picks, target recommendations, auction prices, or claims of 2027 availability.",
        "",
        "The supplied challenge statement requests: "
        '"Build a data-driven system that measures how batters and bowlers perform in high-pressure match situations compared with their usual performance levels."',
        "It also requests two ordered top-10 player lists and a methodology report. Those ranking/submission requirements are recorded here as the challenge statement, but this Step 4C audit does not create or revise rankings.",
        "",
        "## Reference season",
        f"- RR is identified as `team_id={RR_TEAM_ID}` / `Rajasthan Royals` in supplied team and mapping data.",
        f"- Latest represented RR IPL/T20 season: **{reference_season}**, competition `IPL {reference_season}`.",
        f"- Supplied RR match coverage: {len(reference_matches):,} matches.",
        f"- Supplied RR played-player evidence: {len(squad):,} unique contextual player rows and {int(squad['playing_eleven_rows'].sum()):,} player-match rows.",
        "- 2026 is present and therefore used as the cutoff. This is a supplied-data reference season, not a 2027 auction roster.",
        "",
        "## RR squad evidence register",
        "The register is derived from `playing_eleven.is_played`, joined through supplied matches and contextual mapping. The source does not provide a reliable batting/bowling role field, so role is explicitly `UNKNOWN_NOT_INFERRED`.",
        "```text\n" + squad.to_string(index=False) + "\n```",
        "",
        "## Classification method",
        "- RR reference-season participant: the supplied `player_id` has at least one `is_played=True` RR playing-XI record in the selected reference season.",
        "- External historical candidate: the Step 4B context is non-RR and the same supplied `player_id` has no RR participation in the selected reference season.",
        "- Status unresolved: reserved for unmapped or conflicting supplied identity evidence.",
        "- Repeated historical contexts are preserved in classification files. The external pool consolidates only by supplied `player_id` within the Step 4B role, with all source contexts retained.",
        "- Auction status is `NOT_VERIFIED_FROM_SUPPLIED_DATA` for every row.",
        "",
        "## Step 4B classification counts",
        f"- Batters: {len(batters):,} contextual rows; {batters['player_id'].nunique():,} unique supplied players.",
        f"- Bowlers: {len(bowlers):,} contextual rows; {bowlers['player_id'].nunique():,} unique supplied players.",
        f"- RR reference-season participant rows: {int(pd.concat([batters, bowlers]).classification.eq('RR_REFERENCE_SEASON_PARTICIPANT').sum()):,}.",
        f"- External historical candidate rows: {int(pd.concat([batters, bowlers]).classification.eq('EXTERNAL_HISTORICAL_CANDIDATE').sum()):,}.",
        f"- Unresolved rows: {len(unresolved):,}.",
        "",
        "### RR reference-season participants",
        "```text\n"
        + pd.concat(
            [
                batters[batters.classification.eq("RR_REFERENCE_SEASON_PARTICIPANT")],
                bowlers[bowlers.classification.eq("RR_REFERENCE_SEASON_PARTICIPANT")],
            ]
        )[["role", "player_id", "player_name", "context_key", "rr_reference_season_matches"]].to_string(index=False)
        + "\n```",
        "",
        "### External historical candidates",
        "```text\n" + external.to_string(index=False) + "\n```",
        "",
        "## Recruitment relevance and limitations",
        "- The supplied evidence supports an RR reference-season participation register and identifies which Step 4B candidate people were present for RR in 2026.",
        "- It does not support a confirmed 2027 auction target list. No supplied auction pool, retention list, release list, transfer status, purse/budget, overseas-slot data, or official 2027 squad requirement file was found in the audited source set.",
        "- Non-RR historical candidates may be relevant for further investigation, but their availability is unresolved rather than implied.",
        "- Role-based squad-gap analysis is BLOCKED because the supplied sources do not provide a validated role requirement field for recruitment planning. `batting_order`, `is_wk`, and bowling-type delivery fields are not converted into recruitment roles here.",
        "- Pressure evidence remains the Step 4B `chase_baseline` inferred match-state proxy, not validated psychological pressure.",
        "- Bowler economy, conceded runs, official wicket totals, and unsupported composite ratings remain blocked.",
        "",
        "## Exact additional official data required to verify auction eligibility",
        "1. Official 2027 auction-pool or registration list with player IDs/names.",
        "2. Official 2027 retention, release, transfer, and replacement-status records.",
        "3. Official 2027 franchise squads and player-contract/availability status.",
        "4. Official RR roster and role requirements, including overseas-slot and squad-composition constraints if recruitment-gap analysis is required.",
        "",
        "## Identity and integrity checks",
        f"- Player-ID/name consistency audit: {identity_audit.to_dict('records')}.",
        "- Raw CSV SHA-256 hashes were captured before analysis and verified unchanged afterwards.",
        f"- Original challenge statement found: {'yes' if problem_statement else 'no'}.",
        "",
        "## Reproduction",
        "```powershell",
        "python src\\build_step4c_rr_recruitment_audit.py",
        "```",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    raw_hashes_before = {name: sha256(RAW / name) for name in RAW_FILES}
    teams = read_required(RAW / "teams.csv")
    competitions = read_required(RAW / "competitions.csv")
    matches = read_required(RAW / "matches.csv")
    playing_eleven = read_required(RAW / "playing_eleven.csv")
    mapping = read_required(RAW / "competition_team_player_mapping.csv")
    validate_schema(teams, {"comp_id", "team_id", "team_name"}, "teams.csv")
    validate_schema(
        competitions, {"comp_id", "comp_name", "match_format", "season"}, "competitions.csv"
    )
    validate_schema(
        matches, {"match_id", "comp_id", "home_team_id", "away_team_id"}, "matches.csv"
    )
    validate_schema(
        playing_eleven,
        {"match_id", "team_id", "player_id", "is_played", "is_captain", "is_wk", "is_impact"},
        "playing_eleven.csv",
    )
    validate_schema(
        mapping, {"comp_id", "team_id", "player_id", "player_name"}, "competition_team_player_mapping.csv"
    )

    reference_season, reference_matches = establish_reference(
        teams, competitions, matches
    )
    squad, played = build_squad_evidence(
        reference_season, reference_matches, playing_eleven, mapping
    )
    reference_players = played.merge(
        mapping[["comp_id", "team_id", "player_id", "player_name"]].drop_duplicates(),
        on=["comp_id", "team_id", "player_id"],
        how="left",
        validate="many_to_one",
    )
    reference_players["context_key"] = (
        reference_players["comp_id"].astype(str)
        + ":"
        + reference_players["team_id"].astype(str)
        + ":"
        + reference_players["player_id"].astype(str)
    )
    batters = read_required(OUTPUTS / "step4b_batter_candidates.csv")
    bowlers = read_required(OUTPUTS / "step4b_bowler_candidates.csv")
    bat_class, bat_external, bat_unresolved = classify_candidates(
        batters, "batter", reference_players, mapping
    )
    bowl_class, bowl_external, bowl_unresolved = classify_candidates(
        bowlers, "bowler", reference_players, mapping
    )
    external = pd.concat([bat_external, bowl_external], ignore_index=True)
    unresolved = pd.concat([bat_unresolved, bowl_unresolved], ignore_index=True)
    identity_audit = mapping_name_audit(mapping)
    problem_path = REPORTS / "problem_statement.txt"
    problem_statement = problem_path.read_text(encoding="utf-8") if problem_path.exists() else None

    raw_hashes_after = {name: sha256(RAW / name) for name in RAW_FILES}
    if raw_hashes_before != raw_hashes_after:
        raise RuntimeError("Raw CSV hashes changed during Step 4C analysis.")
    outputs = {
        "step4c_rr_squad_evidence.csv": squad,
        "step4c_batter_classification.csv": bat_class,
        "step4c_bowler_classification.csv": bowl_class,
        "step4c_external_candidate_pool.csv": external,
        "step4c_unresolved_status.csv": unresolved,
    }
    for name, output in outputs.items():
        if output.empty and name != "step4c_unresolved_status.csv":
            raise ValueError(f"{name} unexpectedly contains no rows.")
        if output.isna().any().any():
            raise ValueError(f"{name} contains unexplained blank values.")
        output.to_csv(OUTPUTS / name, index=False)
    REPORTS.joinpath("step4c_rr_recruitment_relevance.md").write_text(
        report(
            reference_season,
            reference_matches,
            squad,
            bat_class,
            bowl_class,
            external,
            unresolved,
            identity_audit,
            problem_statement,
            raw_hashes_before,
        ),
        encoding="utf-8",
    )
    print(
        f"Created Step 4C outputs for RR reference season {reference_season}: "
        f"{len(squad)} squad rows, {len(bat_class)} batter rows, "
        f"{len(bowl_class)} bowler rows, {len(external)} external rows, "
        f"{len(unresolved)} unresolved rows."
    )


if __name__ == "__main__":
    main()
